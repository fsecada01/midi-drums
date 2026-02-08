# CI/CD Documentation

## Overview

This project uses **GitHub Actions** for automated testing and continuous integration. Every push to feature branches and pull requests triggers automated tests and linting to ensure code quality.

## Workflow Structure

### File: `.github/workflows/tests.yml`

The CI/CD pipeline consists of 4 jobs:

```
Trigger: Push to main/feat/** or Pull Request
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼───────┐       ┌──────▼──────┐
│  Lint Job     │       │  Test Job   │
│  (Python 3.12)│       │  (Matrix)   │
│               │       │  - Py 3.12  │
│  - ruff       │       │  - Py 3.13  │
│  - black      │       │             │
│  - isort      │       │  Unit Tests │
└───────┬───────┘       │  Integration│
        │               └──────┬──────┘
        │                      │
        └───────────┬──────────┘
                    │
            ┌───────▼───────┐
            │  Test-All Job │
            │  (Python 3.12)│
            │               │
            │  Full Suite   │
            │  + Coverage   │
            └───────┬───────┘
                    │
            ┌───────▼───────┐
            │  Success Job  │
            └───────────────┘
```

## Jobs Breakdown

### 1. Lint Job
**Purpose**: Ensure code style and quality standards

**Steps**:
- Run ruff (fast Python linter)
- Run black (code formatter) in check mode
- Run isort (import sorter) in check mode

**Failure**: Stops PR if linting errors found

### 2. Test Job (Matrix)
**Purpose**: Run tests across multiple Python versions

**Matrix**: Python 3.12 and 3.13

**Steps**:
- Run unit tests with coverage
- Run integration tests separately
- Upload coverage to Codecov (Python 3.12 only)

### 3. Test-All Job
**Purpose**: Run complete test suite with coverage reporting

**Dependencies**: Requires lint and test jobs to pass

**Artifacts**:
- HTML coverage report (7-day retention)

### 4. Success Job
**Purpose**: Final gate confirming all tests passed

## Triggers

**Push Events**:
- main branch
- All feat/** feature branches

**Pull Request Events**:
- PRs targeting main branch

## Coverage Reporting

**Tools**:
- pytest-cov: Collects coverage during test runs
- Codecov: Cloud-based coverage tracking (optional)
- HTML Reports: Downloadable artifacts

**Accessing Reports**:
1. Codecov: https://codecov.io/gh/YOUR_ORG/midi_drums
2. GitHub Artifacts: Actions tab → Download coverage-report

## Local Development

### Running Tests Locally

**Quick test (unit only)**:
```bash
uv run pytest tests/unit -v
```

**Full suite**:
```bash
uv run pytest -v
```

**With coverage**:
```bash
uv run pytest --cov=midi_drums --cov-report=html
```

### Running Linting Locally

**Automated fix**:
```bash
bin/linting.bat  # Windows
bin/linting.sh   # Linux/macOS
```

**Manual commands**:
```bash
uv run ruff check --fix .
uv run black .
uv run isort .
```

**Check only (CI mode)**:
```bash
uv run ruff check .
uv run black --check .
uv run isort --check-only .
```

## Configuration

### GitHub Secrets

**Optional**:
- `CODECOV_TOKEN`: For Codecov integration
  - Generate at https://codecov.io/
  - Add to repository secrets

### Branch Protection

**Recommended settings for main branch**:
- Require status checks before merging
- Require branches up to date
- Status checks required:
  - Linting
  - Tests (Python 3.12)
  - Tests (Python 3.13)
  - Full Test Suite
  - All Tests Passed
- Require pull request reviews (1 approval)
- Require linear history

## Troubleshooting

### Common Failures

**Lint failure**:
```
Error: ruff check . failed
Solution: Run 'uv run ruff check --fix .' locally
```

**Black failure**:
```
Error: black --check . failed
Solution: Run 'uv run black .' locally
```

**Test failure**:
```
Error: pytest failed
Solution: Run 'uv run pytest -v' locally to debug
```

### Workflow Not Triggering

**Check**:
- Branch name matches feat/** pattern
- .github/workflows/tests.yml exists on branch
- Actions enabled in repository settings

### Tests Pass Locally But Fail in CI

**Common causes**:
- Path differences (Windows vs Linux)
- Missing test dependencies
- Environment variables not set

**Debugging**:
1. Run tests in Ubuntu container locally
2. Check workflow logs
3. Add debug prints to failing tests

## Performance

**Cache Strategy**:
- uv cache enabled for faster dependency installation
- First run: ~2-3 minutes (cold cache)
- Subsequent runs: ~30-60 seconds (warm cache)

## Future Enhancements

**Potential additions**:
1. Pre-commit hooks
2. Performance benchmarks
3. Security scanning (Dependabot + CodeQL)
4. Release automation (PyPI publishing)
5. Documentation generation
6. Slack/Discord notifications

## References

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Codecov Documentation](https://docs.codecov.com/)
