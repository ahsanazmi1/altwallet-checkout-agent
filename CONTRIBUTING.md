# Contributing to AltWallet Checkout Agent

Thank you for your interest in contributing to the AltWallet Checkout Agent! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Make (for Unix/Linux) or PowerShell (for Windows)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/altwallet/checkout-agent.git
cd checkout-agent

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (optional but recommended)
pre-commit install
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Quality Checks

**Before submitting a PR, you MUST run these checks:**

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run tests
pytest tests/ -v

# Run smoke tests
pytest tests/smoke_tests.py -v
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Use conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

## Code Quality Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Use Ruff for linting
- Use MyPy for type checking

### Testing Requirements
- All new code must have tests
- Maintain test coverage above 80%
- Include both unit tests and integration tests
- Run smoke tests to ensure basic functionality works

### Documentation
- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Update API documentation if endpoints change

## Pull Request Process

### Before Submitting a PR

1. **Run all quality checks:**
   ```bash
   # Format and lint
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   
   # Run tests
   pytest tests/ -v
   
   # Run smoke tests
   pytest tests/smoke_tests.py -v
   ```

2. **Ensure all tests pass:**
   - Unit tests
   - Integration tests
   - Smoke tests
   - Golden tests

3. **Check code coverage:**
   ```bash
   pytest tests/ --cov=src/altwallet_agent --cov-report=html
   ```

### PR Requirements

- [ ] All quality checks pass (ruff, black, mypy)
- [ ] All tests pass (pytest, smoke tests)
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] Commit messages follow conventional format
- [ ] PR description clearly explains the changes

### PR Review Process

1. **Automated Checks:**
   - GitHub Actions will run all quality checks
   - Tests must pass
   - Code coverage must be maintained

2. **Manual Review:**
   - At least one maintainer must approve
   - Code review feedback must be addressed
   - All conversations must be resolved

3. **Merge Requirements:**
   - All checks pass
   - At least one approval
   - No merge conflicts

## Development Tools

### Available Commands

**Windows (PowerShell):**
```powershell
.\tasks.ps1 help          # Show available commands
.\tasks.ps1 install       # Install dependencies
.\tasks.ps1 test          # Run all tests
.\tasks.ps1 lint          # Run linting
.\tasks.ps1 format        # Format code
.\tasks.ps1 run           # Start API server
```

**Unix/Linux (Make):**
```bash
make help                 # Show available commands
make install              # Install dependencies
make test                 # Run all tests
make lint                 # Run linting
make format               # Format code
make run                  # Start API server
```

### IDE Configuration

**VS Code:**
- Install Python extension
- Configure Black as formatter
- Enable Ruff for linting
- Set up debugging configuration

**PyCharm:**
- Configure external tools for Black and Ruff
- Set up test runner for pytest
- Enable type checking with MyPy

## Getting Help

- **Issues:** Use GitHub Issues for bug reports and feature requests
- **Discussions:** Use GitHub Discussions for questions and general discussion
- **Documentation:** Check the `docs/` directory for detailed guides

## Code of Conduct

Please be respectful and inclusive in all interactions. We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/).

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.
