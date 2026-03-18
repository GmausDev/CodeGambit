# CodeGambit ♟️

AI-powered developer training platform. Sacrifice comfort. Gain depth.

## What is CodeGambit?

CodeGambit is a training environment where developers face controlled coding challenges without AI assistance, get evaluated by an AI engine, and track multi-dimensional skill progression through an ELO rating system.

### Challenge Modes
- **Socratic**: Submit code, AI asks deep questions about your design choices
- **Adversarial**: Find and fix intentional bugs in pre-loaded code
- **Collaborative**: Build incrementally with AI feedback at each step

## Tech Stack
- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: React + Tailwind CSS + Monaco Editor
- **AI Evaluation**: Claude API (Anthropic)
- **Database**: SQLite (local-first)
- **Sandbox**: Docker containers for code execution

## Quick Start

```bash
# Clone
git clone https://github.com/GmausDev/CodeGambit.git
cd CodeGambit

# Backend
cd backend && pip install -e ".[dev]" && cd ..

# Frontend
cd frontend && npm install && cd ..

# Run
make dev
```

## License
MIT
