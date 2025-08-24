# AltWallet Agent for Merchant

AltWallet Agent for Merchant is a lightweight CLI tool that provides deterministic credit card recommendations for individual purchases. The tool analyzes your purchase amount, category, and merchant to recommend the card that will give you the maximum cashback or rewards for that specific transaction.

## Quickstart

### Installation

```bash
# Install from PyPI (when published)
pip install altwallet-merchant-agent

# Or install in development mode
pip install -e .
```

### VS Code/Cursor Setup

This repository includes pre-configured VS Code/Cursor settings in `.vscode/settings.json` that:

- **Python Interpreter**: Points to `.venv\Scripts\python.exe`
- **Pytest**: Enabled with test args set to `["tests"]`
- **Format on Save**: Enabled with Black formatter
- **Linting**: Flake8 enabled with Black-compatible settings
- **Terminal**: PowerShell with auto-activation of virtual environment

**To select the Python interpreter in Cursor:**
1. Open the Command Palette (`Ctrl+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose `.venv\Scripts\python.exe` from the list
4. Alternatively, click on the Python version in the status bar and select the interpreter

The workspace settings will automatically configure the interpreter, but you can manually select it if needed.

### Developer Runbook

**Quick start for each development session:**

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Test CLI (human-readable output)
altwallet-merchant-agent demo -m "Whole Foods" -a 180

# 3. Test CLI (JSON output)
altwallet-merchant-agent demo -m "Whole Foods" -a 180 --json

# 4. Run tests
python -m pytest tests/test_demo.py -v
```

**PowerShell Line Continuation:**
```powershell
# ❌ Wrong - PowerShell doesn't support multi-line flags
altwallet-merchant-agent demo `
  -m "Whole Foods" `
  -a 180 `
  --json

# ✅ Correct - Keep all flags on one line
altwallet-merchant-agent demo -m "Whole Foods" -a 180 --json

# ✅ Alternative - Use backtick for line continuation
altwallet-merchant-agent demo `
  -m "Whole Foods" `
  -a 180 `
  --json
```

### Git Setup

**Step-by-step instructions to initialize Git and push to GitHub:**

```powershell
# 1. Initialize Git repository
git init

# 2. Configure Git user (if not already set)
git config user.name "Your Name"
git config user.email "ahsanazmi@icloud.com"

# 3. Add all files to staging
git add .

# 4. Make the first commit
git commit -m "Initial commit: AltWallet Merchant Agent CLI"

# 5. Create and switch to master branch (if not already on master)
git branch -M master

# 6. Add GitHub remote repository
git remote add origin https://github.com/yourusername/altwallet-merchant-agent.git

# 7. Push to GitHub and set upstream tracking
git push -u origin master
```

**Alternative: Using GitHub CLI (if installed):**
```powershell
# 1. Initialize Git and make first commit (steps 1-5 above)
git init
git add .
git commit -m "Initial commit: AltWallet Merchant Agent CLI"
git branch -M master

# 2. Create GitHub repository and push in one command
gh repo create altwallet-merchant-agent --public --source=. --remote=origin --push
```

**Important Notes:**
- Replace `yourusername` with your actual GitHub username
- Create the GitHub repository named `altwallet-merchant-agent` before running the remote commands
- The `.gitignore` file will automatically exclude `.venv`, `__pycache__`, and other build artifacts
- Use `git status` to check the current state of your repository

### Troubleshooting

**Common Setup Issues and Fixes:**

| Issue | Fix |
|-------|-----|
| **Execution Policy Blocks Scripts** | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| **Venv Activation Fails** | `powershell -ExecutionPolicy Bypass -Command "& .\.venv\Scripts\Activate.ps1"` |
| **Console Script Not Found** | `pip install -e ".[dev]"` (reinstall in editable mode) |
| **Pytest Not Discovering Tests** | `python -m pytest tests/` (use module syntax) |
| **Import Errors (Package Names)** | Check `pyproject.toml` package name matches directory structure |
| **PowerShell "--" Error** | Use `--help` instead of `-help` or `-h` for help flags |
| **Python Interpreter Not Found** | `python -m venv .venv` (ensure Python is in PATH) |
| **Pip Upgrade Fails** | `python -m pip install --upgrade pip --user` |
| **Tests Fail with Typer Errors** | Pass explicit values to CLI functions in tests (not OptionInfo) |
| **JSON Serialization Errors** | Ensure all values in signals dict are JSON-serializable |

**Quick Diagnostic Commands:**
```powershell
# Check Python version and location
python --version
where python

# Check if virtual environment is active
echo $env:VIRTUAL_ENV

# Check installed packages
pip list

# Check if console script is available
Get-Command altwallet-merchant-agent

# Test basic functionality
altwallet-merchant-agent --help
```

### Release Hygiene

This project follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions  
- **PATCH** version for backwards-compatible bug fixes

#### Bumping Version

Update the version in `pyproject.toml`:

```toml
[project]
name = "altwallet-merchant-agent"
version = "0.1.0"  # Change this to new version
```

#### Creating a Release

**1. Update version in pyproject.toml and CHANGELOG.md**

**2. Commit the version bump:**
```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.1.0"
```

**3. Create and push a tag:**
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

**4. Push to main branch:**
```bash
git push origin master
```

#### Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Run tests: `python -m pytest tests/ -v`
- [ ] Test CLI functionality: `altwallet-merchant-agent --help`
- [ ] Commit version bump
- [ ] Create and push git tag
- [ ] Push to main branch

### Complete Setup (Windows PowerShell)

**⚠️ Important PowerShell Notes:**
- Use `.\` for relative paths (not `/`)
- Use `&` to execute scripts: `& ".\script.ps1"`
- PowerShell doesn't support `&&` for command chaining
- Each command must be run separately or use `;` to separate

**Option 1: Automated Setup (Recommended)**
```powershell
# Run the complete setup script
powershell -ExecutionPolicy Bypass -File setup.ps1
```

**Option 2: Manual Setup**
```powershell
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment (PowerShell-specific)
.\.venv\Scripts\Activate.ps1

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install project in editable mode with dev dependencies
pip install -e ".[dev]"

# 5. Test CLI help
altwallet-merchant-agent --help

# 6. Test demo command
altwallet-merchant-agent demo -m "Whole Foods" -a 180 --json

# 7. Run tests
python -m pytest tests/test_demo.py -v
```

**Common PowerShell Mistakes to Avoid:**
```powershell
# ❌ Wrong - PowerShell doesn't support && chaining
python -m venv .venv && .\.venv\Scripts\Activate.ps1

# ❌ Wrong - Use backslashes, not forward slashes
./.venv/Scripts/Activate.ps1

# ❌ Wrong - Missing & for script execution
.\setup.ps1

# ✅ Correct - Separate commands
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# ✅ Correct - Use & for script execution
& ".\setup.ps1"
```

### Usage

Get a card recommendation for a purchase:

```bash
# Basic usage
altwallet-merchant-agent recommend 150.00

# With category and merchant
altwallet-merchant-agent recommend 75.50 --category groceries --merchant "Whole Foods"

# Using short options
altwallet-merchant-agent recommend 200.00 -c travel -m "Delta Airlines"
```

### Demo Command

Get a deterministic demo recommendation with pretend rewards and penalties:

```bash
# Basic demo
altwallet-merchant-agent demo -m "Whole Foods" -a 180

# With custom location
altwallet-merchant-agent demo -m "Shell Gas Station" -a 75 -l "Los Angeles"

# Verbose output
altwallet-merchant-agent demo -m "Delta Airlines" -a 500 -v

# JSON output
altwallet-merchant-agent demo -m "Amazon" -a 100 --json
```

### Examples

```bash
# Grocery shopping
$ altwallet-merchant-agent recommend 120.00 -c groceries -m "Kroger"
💳 AltWallet Card Recommendation
┌─────────────────────────────────────────────────────────────────┐
│ Recommended Card: Amex Blue Cash Preferred                     │
│ Purchase: $120.00 at Kroger                                    │
│ Category: Groceries                                            │
│ Cashback Rate: 6.0% (includes 6.0x category bonus)            │
│ Cashback Amount: $7.20                                         │
└─────────────────────────────────────────────────────────────────┘

# Travel booking
$ altwallet-merchant-agent recommend 500.00 -c travel -m "Expedia"
💳 AltWallet Card Recommendation
┌─────────────────────────────────────────────────────────────────┐
│ Recommended Card: Chase Sapphire Preferred                     │
│ Purchase: $500.00 at Expedia                                   │
│ Category: Travel                                               │
│ Cashback Rate: 2.0% (includes 2.0x category bonus)            │
│ Cashback Amount: $10.00                                        │
└─────────────────────────────────────────────────────────────────┘

# Demo recommendation
$ altwallet-merchant-agent demo -m "Whole Foods" -a 180
🎯 AltWallet Demo Recommendation
┌─────────────────────────────────────────────────────────────────┐
│ Recommended Card: Amex Blue Cash Preferred                     │
│ Score: 5.40                                                    │
└─────────────────────────────────────────────────────────────────┘
               Signals
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Signal               ┃ Value       ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Merchant             │ Whole Foods │
│ Location             │ New York    │
│ Rewards Value Usd    │ $5.40       │
│ Merchant Penalty Usd │ $0.00       │
└──────────────────────┴─────────────┘
```

### Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black altwallet_merchant_agent/
isort altwallet_merchant_agent/

# Lint code
flake8 altwallet_merchant_agent/
```

### Running Tests in Cursor's Terminal (Windows PowerShell)

To run the unit tests in Cursor's integrated terminal on Windows PowerShell:

```powershell
# Navigate to the project directory
cd "C:\Users\[YourUsername]\Desktop\altwallet checkout agent"

# Activate virtual environment (if using one)
.\.venv\Scripts\Activate.ps1

# Install development dependencies (if not already installed)
pip install -e ".[dev]"

# Run all tests
python -m pytest tests/test_demo.py -v

# Run specific test class
python -m pytest tests/test_demo.py::TestDemoCommand -v

# Run specific test method
python -m pytest tests/test_demo.py::TestDemoCommand::test_demo_context_creation -v

# Run tests with coverage
python -m pytest tests/test_demo.py --cov=altwallet_merchant_agent --cov-report=term-missing

# Run tests in parallel (faster)
python -m pytest tests/test_demo.py -n auto
```

**Test Categories**:
- `TestCardRecommender`: Tests the core recommendation engine
- `TestPurchase`: Tests the Purchase dataclass
- `TestCard`: Tests the Card dataclass  
- `TestDemoCommand`: Tests the demo command functionality

**Key Test Validations**:
- ✅ Context creation with merchant="Whole Foods", amount=180.0, location="New York"
- ✅ Recommended card is a non-empty string
- ✅ Score is a float value
- ✅ Signals contain all four required fields (merchant, location, rewards_value_usd, merchant_penalty_usd)
- ✅ Scores are deterministic for the same inputs
- ✅ Different inputs produce different scores
- ✅ Demo calculation logic (3% base reward, 0 penalty)

## Features

- **Deterministic Recommendations**: Same inputs always produce the same recommendation
- **Category Bonuses**: Considers category-specific bonus rewards
- **Annual Fee Calculation**: Factors in monthly cost of annual fees
- **Beautiful Output**: Rich terminal formatting with tables and panels
- **Easy to Extend**: Simple card database that's easy to modify
- **Demo Mode**: Deterministic demo recommendations with pretend rewards

## Supported Cards

The tool currently includes these popular cards:
- Chase Freedom Unlimited (1.5% on all purchases)
- Chase Sapphire Preferred (2.5x on travel)
- Citi Double Cash (2% on all purchases)
- Amex Blue Cash Preferred (6% on groceries)

## License

MIT License - see LICENSE file for details.
