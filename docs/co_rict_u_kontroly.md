# Co říct u 1. kontroly (kroky 1–3)

## Úvod (15 s)
„NurseShift je webová aplikace pro plánování 12hodinových směn zdravotních sester. Vrchní sestra dnes sestavuje rozpis ručně v Excelu a hlídá pravidla z hlavy. Moje aplikace to zjednoduší a pravidla pohlídá sama.“

## Krok 1 – Specifikace a příprava (~1 min)
- Mám hotové finální PRD: role (admin, vrchní sestra, sestra), datový model ve Firestore, business logika.
- Kód je na GitHubu: https://github.com/MjjeGoat/NurseShift
- Mám návrh obrazovek: přihlášení, měsíční matice směn, pohled sestry, správa uživatelů a nastavení oddělení. *(ukázat `docs/navrh_obrazovek.html`)*

## Krok 2 – Kostra projektu a Docker (~1,5 min)
- Celé prostředí se spustí jedním příkazem `docker compose up --build`.
- Běží tři služby: FastAPI backend, React frontend a Firestore Emulator, takže nepotřebuju skutečný Google Cloud.
- Seed skript při startu naplní databázi 12 testovacími sestrami, nastavením oddělení a ukázkovým rozpisem.
- **Ukázka:** otevřít http://localhost:5173 (stav backendu + seznam seed uživatelů).

## Krok 3 – Backend API a databáze (~2 min)
- Datové modely jsou v Pydanticu, který validuje vstupy (např. úvazek 0,1–1,5, formát měsíce).
- CRUD uživatelů: přidávat, upravovat a mazat smí jen admin.
- Nastavení oddělení: délka směny, minimální obsazenost, pravidla. Mění ho admin nebo vrchní sestra.
- Měsíční rozpis se ukládá a načítá po měsících (`/api/schedules/2026-11`). Ukládat smí jen vrchní sestra nebo admin.
- **Ukázka:** http://localhost:8001/docs (Swagger). Vyzkoušet GET `/api/users`, pak PUT rozpisu. Dev přihlášení přes hlavičku `X-Dev-User-Id`.
- Mám 5 automatických testů (`pytest`) a všechny procházejí.

## Závěr (15 s)
„Kroky 1–3 jsou splněné. Další krok je validátor pravidel a manuální plánování v matici.“

## Možné otázky
- **Proč Firestore?** Je schema-less, hodí se na měsíční rozpisy jako dokumenty, a existuje emulátor pro lokální vývoj.
- **Jak je řešené přihlášení?** Cílově Microsoft Entra ID nemocnice, teď dev režim s testovacími účty.
- **Proč port 8001?** Port 8000 mám obsazený jiným projektem.

## Před kontrolou
1. `cd kontrola_krok_1-3; docker compose up -d`
2. Otevřít: `localhost:5173`, `localhost:8001/docs`, `docs/navrh_obrazovek.html`, GitHub repo.
