# Projektová dokumentace: Systém pro plánování směn sester (NurseShift)

## 1. Přehled projektu (Project Overview)
Webová aplikace pro plánování, správu a optimalizaci 12hodinových služeb zdravotních sester na oddělení. Systém kombinuje manuální plánování v přehledné matici s automatickým generátorem rozpisů, hlídáním minimální obsazenosti, správou preferencí sester a systémem pro vzájemné výměny směn.

## 2. Technologický Stack (Tech Stack)
* **Frontend:** React (Vite, TypeScript), Tailwind CSS (pro rychlý a čistý UI design matice), React Router, Axios/Fetch pro komunikaci s API.
* **Backend:** Python 3.11+ (FastAPI), Pydantic (validace dat).
* **Databáze:** Google Cloud Firestore (NoSQL dokumentová databáze – pro lokální vývoj využít *Firebase Local Emulator Suite* v Dockeru).
* **Autentizace:** Microsoft účet nemocnice (Microsoft Entra ID / Azure AD – OAuth2 / OIDC pomocí MSAL na frontendu a validace JWT tokenů na backendu + podpora lokálního dev přihlášení pro testování bez aktivního Azure tenanta).
* **Exporty:** `openpyxl` (generování `.xlsx` rozpisů na backendu) a `ReportLab` / `WeasyPrint` (generování `.pdf`).
* **Infrastruktura:** Docker & `docker-compose` (kontejnery pro `frontend`, `backend` a `firestore-emulator`).

---

## 3. Uživatelské role a oprávnění (RBAC)
1. **Admin:**
   * Správa uživatelů (vytváření účtů, spárování s nemocničním Microsoft účtem, přiřazování rolí a úvazků).
   * Globální nastavení systému a parametrů oddělení (definice minimální obsazenosti pro denní/noční směny).
2. **Vrchní sestra (Head Nurse):**
   * Tvorba a editace měsíčního rozpisu směn (manuální klikání v matici + spuštění automatického generátoru).
   * Přehled požadavků (preferencí a dovolených) od sester.
   * Schvalování/zamítání žádostí o výměnu směn mezi sestrami.
   * Publikování hotového rozpisu a export do Excelu / PDF.
3. **Sestra (Nurse):**
   * Zobrazení publikovaného rozpisu (celkového i vlastního osobního kalendáře).
   * Zadávání měsíčních preferencí před uzávěrkou (chci sloužit / nemohu sloužit / dovolená).
   * Žádost o výměnu směny s jinou sestrou v již publikovaném rozpisu.

---

## 4. Datový model (Firestore Collections)

Jelikož používáme NoSQL Firestore, data budou strukturována do následujících hlavních kolekcí:

### `users` (Dokument ID = `user_id`)
```json
{
  "name": "Bc. Jana Nováková",
  "email": "jana.novakova@nemocnice.cz",
  "microsoft_oid": "00000000-0000-0000-0000-000000000001",
  "role": "nurse",
  "workload": 1.0,
  "active": true
}
```
*Poznámka:* `role` může nabývat hodnot `"admin"` | `"head_nurse"` | `"nurse"`. `workload` reprezentuje úvazek (např. `1.0` plný, `0.5` poloviční). Uživatelé se autentizují přes nemocniční Microsoft účet (spárování přes `microsoft_oid` nebo `email`).

### `settings` (Dokument ID = `department_config`)
```json
{
  "shift_duration_hours": 12,
  "min_staff_day": 3,
  "min_staff_night": 2,
  "weekly_hours_full_workload": 37.5,
  "rules_config": {
    "prevent_night_to_day": true,
    "max_consecutive_shifts": 3
  }
}
```

### `schedules` (Dokument ID = `YYYY-MM`, např. `2026-11`)
Obsahuje stav měsíčního rozpisu a samotné přiřazení směn.
```json
{
  "year": 2026,
  "month": 11,
  "status": "draft",
  "shifts": {
    "2026-11-01": {
      "day": ["user_id_1", "user_id_2", "user_id_3"],
      "night": ["user_id_4", "user_id_5"],
      "vacation": ["user_id_6"]
    }
  }
}
```
*Poznámka:* `status` může nabývat hodnot `"open_for_preferences"` | `"draft"` | `"published"`.

### `preferences` (Dokument ID = `YYYY-MM_user_id`)
Požadavky sester na daný měsíc.
```json
{
  "user_id": "user_id_1",
  "year_month": "2026-11",
  "requests": {
    "2026-11-05": "unavailable",
    "2026-11-12": "prefer_day"
  },
  "note": "5.11. mám lékaře"
}
```
*Poznámka:* Hodnoty v `requests` mohou být `"prefer_day"` | `"prefer_night"` | `"unavailable"` | `"vacation"`.

### `swap_requests` (Dokument ID = `auto_id`)
Žádosti o prohození směny.
```json
{
  "schedule_id": "2026-11",
  "requester_id": "user_id_1",
  "requester_date": "2026-11-10",
  "requester_shift": "day",
  "target_nurse_id": "user_id_2",
  "target_date": "2026-11-14",
  "target_shift": "day",
  "status": "pending_nurse",
  "created_at": "2026-10-16T08:00:00Z"
}
```
*Poznámka:* Workflow stavu `status`: `"pending_nurse"` -> `"pending_head_nurse"` -> `"approved"` / `"rejected"`.

---

## 5. Klíčová Business Logika a Funkce

### A. Směny a Matice (UI/UX návrh)
* **Nepřetržitý provoz (24/7 včetně víkendů):**
  * Směny jsou 12hodinové (denní a noční) a plánují se na všechny dny v týdnu včetně sobot a nedělí.
  * Měsíční fond pracovní doby se počítá dle nepřetržitého provozu (37,5 h týdně = 7,5 h × počet pracovních dnů Po–Pá v daném měsíci × `workload`), každá odsloužená směna (`D`, `N`) i celodenní dovolená (`DOV`) započítává 12 hodin.
* **Typy buněk v matici:**
  * `D` – Denní směna (12 h, např. 06:00 – 18:00, modrá barva)
  * `N` – Noční směna (12 h, např. 18:00 – 06:00, tmavě fialová/šedá)
  * `DOV` – Dovolená (12 h, zelená)
  * `V` / Prázdné – Volno
* **Hlavní obrazovka (Plánovací matice):**
  * **Řádky:** Jména sester + sloupec s počtem naplánovaných hodin v daném měsíci (porovnání s fondem pracovní doby dle úvazku).
  * **Sloupce:** Dny v měsíci (1 až 30/31), víkendy vizuálně podbarvené (se stejnou minimální obsazeností pro nepřetržitý provoz).
  * **Spodní součtové řádky:** Pod tabulkou jsou 2 řádky: *Obsazenost Denní* a *Obsazenost Noční*. Pokud v daný den klesne počet sester pod limit z `department_config` (např. méně než 3 na denní), buňka svítí červeně (varování).
  * **Zobrazení preferencí v matici:** Když vrchní sestra tvoří rozpis, v buňkách vidí jemný podkres nebo ikonku toho, co si sestra přála (např. přeškrtnutý kroužek = sestra nemůže).

### B. Manuální plánování + Modulární Validátor (`ShiftValidator`)
* Vrchní sestra klikáním do buněk přepíná stavy (`Prázdné` -> `D` -> `N` -> `DOV`).
* Na backendu (i frontendu) bude připravená třída `ShiftValidator`, která vrací seznam varování (`warnings`). Hlídá:
  1. **Minimální obsazenost** (na denní i noční je dostatek lidí v každý den včetně víkendů).
  2. **Kolize se žádostí sestry** (sestra má zadané `unavailable`, ale dostala směnu).
  3. **Odpočinek po noční směně (`prevent_night_to_day`)** – zákaz denní směny (`D`) bezprostředně po noční směně (`N`) z předchozího dne.
  4. **Maximální počet směn v řadě (`max_consecutive_shifts`)** – varování při překročení povoleného počtu po sobě jdoucích směn (výchozí limit 3).
* *Architektonická příprava:* Do `ShiftValidator` půjde v budoucnu snadno přidávat další metody (např. `check_max_overtime()`), aniž by se musel přepisovat zbytek aplikace.

### C. Automatický generátor rozpisu (`ScheduleGenerator`)
* Tlačítko **"Automaticky doplnit rozpis"** pro vrchní sestru.
* Algoritmus (heuristika / constraint satisfaction):
  1. Načte již ručně zadané směny a dovolené (ty jsou neměnné – zafixované).
  2. Projde všechny dny v měsíci (včetně víkendů) od 1. do posledního.
  3. Doplní do každého dne sestry na `D` a `N` tak, aby byla splněna minimální obsazenost, neporušily se preference `unavailable`, dodržela se pravidla `prevent_night_to_day` a `max_consecutive_shifts`, zohlednily se preference `prefer_day` / `prefer_night` a hodiny se rozdělovaly rovnoměrně podle výše úvazku (`workload`).

### D. Výměny směn (Workflow)
1. Sestra A klikne na svou směnu a vybere „Požádat o výměnu“ -> vybere Sestru B a její směnu (nebo volný den).
2. Sestra B potvrdí, že s výměnou souhlasí (`pending_head_nurse`).
3. Vrchní sestra uvidí v notifikacích žádost, systém jí ukáže, zda výměna nerozbije obsazenost, a jedním klikem ji schválí (`approved`) -> směny se v `schedules` automaticky prohodí.

### E. Exporty
* Endpoint `GET /api/schedules/{year_month}/export/excel` vygeneruje pomocí `openpyxl` naformátovanou tabulku (včetně barev a součtů hodin) připravenou k tisku na A4 na šířku.
* Endpoint `GET /api/schedules/{year_month}/export/pdf` vygeneruje PDF verzi.

---

## 6. Implementační plán (Roadmap)

1. **[x] Krok 1: Kostra projektu & Docker (HOTOVO)**
   * Vytvoření adresářové struktury (`/backend`, `/frontend`), `docker-compose.yml` (FastAPI, React Vite, Firebase/Firestore Emulator) a napojení Pythonu na Firestore + seed testovacích dat.
2. **[x] Krok 2: Backend API – Uživatelé, Nastavení a Základní CRUD rozpisu (HOTOVO)**
   * Modely v Pydanticu, Microsoft Entra ID autentizace (`/api/auth/*`), endpointy pro správu sester (`/api/users`), konfiguraci obsazenosti (`/api/settings`), preference (`/api/preferences`) a načtení/uložení měsíčního rozpisu (`/api/schedules`) včetně kompletního `ShiftValidator`.
3. **[x] Krok 3: Frontend – Plánovací matice a Preference (HOTOVO)**
   * Vytvoření hlavního React komponentu `ShiftMatrix` (interaktivní tabulka s režimem přepínání i štětce, podkres preferencí, součty hodin vs. fond a obsazenost D/N), přihlašovací lišty s přepínačem nemocničních Microsoft účtů, pohled pro sestry `PreferencesPanel` a pohled pro Admina `AdminPanel`.
4. **[x] Krok 4: Automatický generátor a Modulární validátor (HOTOVO)**
   * Implementace `ShiftValidator` (`backend/app/services/validator.py`) a `ScheduleGenerator` (`backend/app/services/generator.py`) + endpoint `POST /api/schedules/{year_month}/generate` a napojení na tlačítko *Automaticky doplnit rozpis* v `ShiftMatrix`.
5. **[x] Krok 5: Výměny směn a Export do Excelu/PDF (HOTOVO)**
   * Dokončení backend/frontend workflow pro výměny směn (`/api/swaps`, `SwapsPanel.tsx`) se simulací dopadu přes `ShiftValidator` a vytvoření exportních endpointů (`GET /api/schedules/{year_month}/export/excel` a `GET /api/schedules/{year_month}/export/pdf` v `exporter.py`).

---

## 7. Aktuální stav rozpracovanosti (Beta verze kompletní)
* **Poslední dokončený krok:** Krok 5 (Výměny směn + Exporty do Excelu `.xlsx` a PDF `.pdf`) – dne 16. 10. 2026. **Všech 5 kroků Beta verze je hotových.**
* **Co je hotové a funkční:**
  * `docker-compose.yml`, `.env.example`, `.gitignore`
  * Backend v `/backend/app/`:
    * `config.py`, `db.py` (Firestore Emulator + automatický lokální JSON fallback `LocalFirestoreClient`)
    * `seed.py` (12 uživatelů s `microsoft_oid`, `department_config` pro 12h nepřetržitý provoz Po–Ne, preference, demo rozpis `2026-11` a vzorová žádost o výměnu)
    * `models.py`, `auth.py`, `routers/auth.py`, `routers/users.py`, `routers/settings.py`, `routers/preferences.py`, `routers/schedules.py`, `routers/swaps.py`
    * `services/validator.py` (`ShiftValidator`), `services/generator.py` (`ScheduleGenerator`), `services/exporter.py` (Excel `.xlsx` přes `openpyxl` a PDF `.pdf` přes `reportlab`)
  * Frontend v `/frontend/src/`:
    * `types.ts`, `api.ts`, `App.tsx`
    * `components/ShiftMatrix.tsx` (plánovací matice 12h směn D/N/DOV/V, tlačítko *Automaticky doplnit rozpis*, exporty *Excel (.xlsx)* a *PDF (.pdf)*, zvýraznění víkendů, obsazenosti a varování)
    * `components/PreferencesPanel.tsx` (zadávání preferencí sestrami + přehled požadavků pro vrchní sestru)
    * `components/SwapsPanel.tsx` (třífázové workflow výměny směn mezi sestrami se simulací dopadu a schválením vrchní sestrou)
    * `components/AdminPanel.tsx` (správa uživatelů, úvazků a parametrů oddělení)
* **Spuštění aplikace:**
  ```bash
  docker compose up --build
  ```
  * Frontend: `http://localhost:5173`
  * Backend API & Swagger dokumentace: `http://localhost:8000/docs`
  * Firestore Emulator: `http://localhost:8080`