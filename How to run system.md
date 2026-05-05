To run the complete system:

# Terminal 1: Backend server

python -m uvicorn Backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend dev server

cd Frontend && npm run dev

# Then visit: http://localhost:5173
