# Upgrade from the working v2 project

This release is designed to be extracted **over the current working project**.

It intentionally excludes:

- `backend/.env`
- `backend/credentials.json`
- `backend/token.json`
- `backend/dev.db`
- `backend/.venv/`

So the existing live Gmail/Shopify credentials and local database stay on the machine.

After extraction:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts\init_db.py
python -m pytest -q
python scripts\evaluate.py
uvicorn app.main:app --reload
```

Frontend:

```powershell
cd frontend
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500
```

`init_db.py` is required once after this upgrade because v3 adds additive tables for:

- human corrections
- Automation Lab simulations

Existing v2 case data is preserved.
