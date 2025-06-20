# ChoicePilot

ChoicePilot is an application that combines a FastAPI backend with a React frontend.

## Directory overview
- **backend/** – FastAPI service and related utilities.
- **frontend/** – React application created with Create React App.
- **scripts/** – helper scripts for development.
- **tests/** – automated test suite.

## Prerequisites
- **Python 3.11+**
- **Node.js 20+** with `yarn` or `npm`
- **Docker** (optional for containerised runs)

## Installation
1. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Install frontend dependencies:
   ```bash
   cd frontend
   yarn install  # or npm install
   cd ..
   ```
3. Copy the example environment files and populate them with your values:
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
   Important variables include `SUPABASE_URL`, `SUPABASE_KEY`, `MONGO_URL`, and `REACT_APP_BACKEND_URL`.

## Running the application
- **Backend**
  ```bash
  uvicorn server:app --app-dir backend --reload --port 8001
  ```
- **Frontend**
  ```bash
  cd frontend
  yarn start  # or npm start
  ```

The React app will be available on <http://localhost:3000> and will talk to the FastAPI backend on port `8001`.

You can also build and run everything using Docker:
```bash
docker build -t choicepilot .
docker run -p 3000:80 -p 8001:8001 choicepilot
```

## Running tests
- Backend tests:
  ```bash
  pytest
  ```
- Frontend tests:
  ```bash
  cd frontend && yarn test
  ```
