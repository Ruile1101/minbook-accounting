# Min Book Shop Accounting

Local, single-user accounting for a Malaysian print and stationery shop. No login is required. Accounting data and ShopPOS data are kept in separate databases.

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows)
3. Copy `.env.example` to `.env`, then set `ACCOUNTING_DATABASE_URL`. SQLite is supported locally.
4. Install: `pip install -r requirements.txt`
5. Start: `python run.py`
5. Open `http://127.0.0.1:5000`

The application creates its accounting tables automatically. It does not insert demo transactions.

## ShopPOS (read-only) sync

Set `SHOPPOS_DATABASE_URL` in `.env` to the existing ShopPOS PostgreSQL URL, then open `/shoppos`, use **Test Connection**, and **Sync ShopPOS Sales**. The integration reads ShopPOS's verified `sale` and `sale_item` tables only; it never runs migrations or writes to ShopPOS. An accounting-side unique source reference prevents duplicate imports.

Run tests with `pytest -q`.
