.PHONY: setup dev dev-backend dev-frontend test test-backend lint build clean

setup:
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -v
	cd frontend && npm test

test-backend:
	cd backend && pytest -v

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

build:
	cd frontend && npm run build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -f backend/*.db
