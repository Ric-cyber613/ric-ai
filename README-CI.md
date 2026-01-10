# Continuous Integration (CI)

This repository includes a GitHub Actions workflow that runs tests on push and pull requests to `main`.

## What it runs
- Unit tests: `pytest -q`
- (Optional) Gated integration tests: set repository variable `RUN_HF_INTEGRATION_TESTS=true` to run HF integration tests during the job.

## How to enable gated integration tests
1. Go to your repository Settings → Secrets and variables → Actions → Variables (or use Secrets)
2. Add a variable `RUN_HF_INTEGRATION_TESTS` with value `true` to enable running integration tests on CI.

## Notes
- The workflow uses a Python matrix: 3.9, 3.10, 3.11.
- Pip caching is enabled to speed up runs.
- The CI now includes a lint job (Black + Flake8) and pytest runs with coverage and JUnit XML output for better visibility in Actions.

## Preventing committed Python caches
The CI now checks for any committed Python cache files (`__pycache__`, `.pyc`, `.pyo`) and will fail the job if any are present.

To remove already tracked cache files locally, run:

```bash
# remove tracked __pycache__ directories and .pyc files
git rm --cached -r **/__pycache__ || true
git rm --cached -r **/*.pyc || true

# commit the removal
git commit -m "chore: remove tracked Python cache files"

# push the fix
git push origin main
```

If you prefer I can do this for you; however the environment I'm running in sometimes cannot run git commands, so please run the above locally if my automated attempts fail.