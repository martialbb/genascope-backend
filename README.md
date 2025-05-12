# CancerGenix Backend

This is the backend repository for the CancerGenix application, built with FastAPI and Python.

## 🔄 Related Repositories

This project is part of a multi-repository architecture:
- Backend (this repo): API server for the CancerGenix application
- Frontend: [cancer-genix-frontend](https://github.com/martialbb/cancer-genix-frontend) - Astro/React UI

## 🚀 Project Setup

```sh
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                 | Action                                           |
| :---------------------- | :----------------------------------------------- |
| `uvicorn app.main:app --reload` | Start development server at `localhost:8000` |
| `pytest`                | Run tests                                        |
| `alembic upgrade head`  | Run database migrations                          |

## 🔌 Frontend Connection

This backend is designed to work with the [cancer-genix-frontend](https://github.com/martialbb/cancer-genix-frontend) repository.

Make sure to configure CORS in `app/main.py` to allow requests from your frontend application.
