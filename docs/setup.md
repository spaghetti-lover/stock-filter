# Backend
Use this way to run backend
1. `cd backend`
2. `python -m venv venv` in window, `python3 -m venv venv` in linux
3. `source .venv/bin/activate`
4. `pip install -r requirements`
5. `.venv\Scripts\Activate.ps1` in window, `source .venv/bin/activate` in linux
6. `uvicorn main:app --reload` to run

# Run both frontend and backend after setup
## Terminal 1 — backend
cd backend && uvicorn main:app --reload

## Terminal 2 — frontend
cd frontend && streamlit run app.py
