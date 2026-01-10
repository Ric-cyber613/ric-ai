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
- If you'd like, I can add a lint job and upload junit xml test reports to the Actions UI for easy inspection.