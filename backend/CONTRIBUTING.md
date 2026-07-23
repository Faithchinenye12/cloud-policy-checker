# Contributing to Cloud Policy Checker

Thank you for your interest in contributing!

## Development Setup

1. Clone the repository
2. Copy .env.example to .env
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Run tests: `pytest`

## Code Standards

- Python code must pass ruff and mypy checks
- Minimum 80% test coverage required
- All commits must be atomic and well-described
- Pull requests require review before merging

## Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Write tests
4. Ensure all tests pass: `pytest`
5. Run linting: `ruff check backend/app`
6. Run type checking: `mypy backend/app`
7. Commit your changes
8. Push to your fork
9. Submit a pull request

## Questions?

Open an issue on GitHub.