# NurseShift – stav k 1. kontrole (kroky 1–3)

Systém pro plánování 12h směn sester. Tato složka obsahuje pouze to, co plán projektu požaduje k 1. kontrole.

## Krok 1 – Specifikace a příprava (říjen 2026)
- [x] Finální PRD: [specifikace_projektu_nurseshift.md](specifikace_projektu_nurseshift.md)
- [x] Git repozitář (lokálně inicializován; `git remote add origin <URL>` + `git push -u origin main` pro GitHub)
- [x] Návrh obrazovek: [docs/navrh_obrazovek.md](docs/navrh_obrazovek.md)

## Krok 2 – Kostra projektu a Docker (listopad, 1.–2. týden)
- [x] `docker-compose.yml`: FastAPI backend, React (Vite) frontend, Firestore Emulator
- [x] Seed skript s testovacími sestrami: `backend/app/seed.py` (12 uživatelů, nastavení oddělení, ukázkový rozpis; spouští se automaticky `AUTO_SEED=true` nebo `POST /api/seed`)

Spuštění: `docker compose up --build` → frontend http://localhost:5173, API docs http://localhost:8000/docs
Bez Dockeru (Windows): `./start_local.ps1` (použije lokální fallback úložiště místo emulátoru)

## Krok 3 – Backend API a databáze (listopad, 3.–4. týden)
- [x] Pydantic modely: `backend/app/models.py`
- [x] CRUD uživatelů: `GET/POST /api/users`, `PUT/DELETE /api/users/{id}` (POST/PUT/DELETE jen admin)
- [x] Nastavení oddělení: `GET/PUT /api/settings` (PUT admin / vrchní sestra)
- [x] Ukládání a načítání měsíčního rozpisu: `GET/PUT /api/schedules/{YYYY-MM}`
- Přihlášení v dev režimu: hlavička `X-Dev-User-Id` (např. `user_admin`, `user_head`, `user_1`) nebo `POST /api/auth/dev-login`.
- Testy: `cd backend; pip install -r requirements.txt; pytest` (5 testů: seed, CRUD uživatelů, nastavení, rozpis)
