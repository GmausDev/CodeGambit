.PHONY: setup dev dev-backend dev-frontend test test-backend lint build clean

# nvm setup for Node.js commands
NVM_INIT = export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"

# venv setup for Python commands
VENV_INIT = cd backend && ([ -d .venv ] && . .venv/bin/activate || true)

setup:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	$(NVM_INIT) && cd frontend && npm install

dev-backend:
	$(VENV_INIT) && uvicorn app.main:app --reload --port 8000

dev-frontend:
	$(NVM_INIT) && cd frontend && npm run dev

test:
	$(VENV_INIT) && pytest -v
	$(NVM_INIT) && cd frontend && npm test

test-backend:
	$(VENV_INIT) && pytest -v

lint:
	$(VENV_INIT) && ruff check .
	$(NVM_INIT) && cd frontend && npm run lint

build:
	$(NVM_INIT) && cd frontend && npm run build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	rm -f backend/*.db
