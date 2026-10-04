# Sahaay

Sahaay is a full-stack hackathon MVP for financial safety and accessibility. It uses simulated users, accounts, contacts, transactions, schemes, alerts, and payments only. It never requests banking credentials, UPI PINs, or real money.

## Structure

- `frontend/` — React, TypeScript, Vite and Tailwind UI.
- `backend/app/main.py` — FastAPI routers, seeded demo repository, scam rules and confirmation-safe payment flow.
- `public/manus-routes.json` — Preview route manifest.
- `TODO.md` — approved MVP outcomes.

## Run locally

```bash
cd frontend
npm install
npm run build
cd ../backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

For frontend hot reload, run `npm run dev` in `frontend/` and use the Vite proxy to FastAPI on port 8000. For the managed Preview, build the frontend first; FastAPI serves `frontend/dist` and the `/api/*` routes from one origin.

## Environment

Copy `.env.example` to `.env`. The Preview uses the configured managed MySQL database when a `mysql://` URL is present, and supports PostgreSQL via `postgresql+psycopg://`. In either case, the startup hook creates the same tables from `backend/app/models.py` and seeds realistic demo data. SQLite (`sahaay_demo.sqlite3`) remains the local fallback when no database URL is supplied. `GEMINI_API_KEY` enables the isolated Gemini adapter; if it is absent or unavailable, the assistant uses the safe deterministic fallback.

Scam Check uses a small simulated labeled corpus in `backend/app/services/scam_training_data.py` and a cached TF-IDF + Logistic Regression model in `backend/app/services/scam_ml.py`. The model is trained or loaded once during startup and saved under the ignored `backend/app/services/artifacts/` directory. The current holdout metrics are accuracy `0.875`, precision `1.0`, recall `0.75`, and F1 `0.8571`; these are MVP demo metrics, not production performance claims.

## Safety architecture

Assistant requests become structured intent data only. Backend validation and safety checks happen before a review payload is returned. The simulated payment completion endpoint requires a server-issued confirmation token created by `/api/payments/prepare`, and only an explicit user confirmation calls `/api/payments/confirm`. No endpoint connects to a bank, UPI, or real money.
