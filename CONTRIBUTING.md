# Contributing to VLAI LLM Serving

This is the quick-start guide for developers contributing to VLAI LLM Serving. For branch, review, CI, and release policies, see [Development Workflow](docs/development-workflow.md).

> **Project status:** The FastAPI proxy and mocked tests are available, but the application is still in development and is not ready for public access.

## 1. Get the code

You need Git, Conda (or Miniconda), and Python 3.12. A GPU and Docker are **not required** for ordinary backend development or the current mocked tests.

```bash
git clone https://github.com/Datyth/VLAI-LLM-Serving.git
cd VLAI-LLM-Serving
git switch develop
git pull --ff-only origin develop

conda env create -f environment.yml
conda activate vlai-llm
python -m pip install -e '.[dev]'
cp .env.example .env
```

The default `.env` points to vLLM at `http://127.0.0.1:8000`. Do not commit `.env`, API keys, or other secrets.

## 2. Run the checks locally

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check src tests
```

The current automated tests mock the upstream vLLM server. They do not validate real GPU inference or production readiness.

## 3. Pick an issue and make a branch

Start with a GitHub Issue where possible. Use the latest `develop`:

```bash
git status                  # Ensure there are no uncommitted changes
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c feat/your-feature-name
```

Branch naming examples:

| Prefix | For | Example |
| --- | --- | --- |
| `feat/` | New functionality | `feat/api-key-auth` |
| `fix/` | Development bug fix | `fix/streaming-disconnect` |
| `test/` | Automated tests | `test/proxy-timeout` |
| `docs/` | Documentation | `docs/client-onboarding` |
| `chore/` | CI and maintenance | `chore/github-actions` |
| `hotfix/` | Urgent fixes from `main` | `hotfix/proxy-502` |

Avoid pushing directly to `main` or `develop`. Only urgent hotfix branches should start from `main`.

## 4. Develop and submit a PR

Keep changes focused. Add tests for changed behavior and update documentation when interfaces or setup steps change. Run the checks above before pushing.

```bash
git add -A
git diff --cached --stat
git commit -m "feat: add API key authentication"
git push -u origin feat/your-feature-name
```

On GitHub:

1. Open a Pull Request with **base: `develop`** and **compare: your branch**.
2. Describe the change, how you tested it, any deployment impact, and the related Issue.
3. Request a reviewer when required by branch protection.
4. Check that the `backend-checks` GitHub Actions job passes.
5. Respond to feedback, push fixes to the same branch, and wait for approval.
6. **Squash and merge** into `develop` after all required checks and reviews pass, then delete the topic branch.

PR authors cannot approve their own PR to satisfy required approvals. If your team currently has only one contributor, the repository owner must configure rules accordingly rather than bypassing them.

After merging, refresh your local branch:

```bash
git switch develop
git pull --ff-only origin develop
```

## 5. Optional: local GPU inference

Only use this on an approved GPU machine with Docker and NVIDIA Container Toolkit installed.

```bash
# Terminal A
bash scripts/run_vllm.sh

# Terminal B
conda activate vlai-llm
python -m uvicorn llm_api.main:app --host 127.0.0.1 --port 8001 --reload
```

See [Deployment Guide](docs/deployment.md) and [API Reference](docs/api.md) for validation commands. `/health` checks FastAPI liveness, **not** model readiness. Keep the service bound to localhost unless security controls have been implemented and access has been approved.

## 6. Contribution checklist

- [ ] Changes are scoped to one logical task.
- [ ] New or changed behavior has appropriate tests.
- [ ] `pytest` and Ruff checks pass locally.
- [ ] User-facing or operational changes are documented.
- [ ] No credentials, model weights, datasets, personal data, or private logs are committed.
- [ ] The PR includes testing evidence and describes compatibility and deployment risks.

## 7. Reference documents

- [README](README.md): Overview and local quick start.
- [Development Workflow](docs/development-workflow.md): Branch strategy, reviews, CI, and releases.
- [Architecture](docs/architecture.md): Request flows and component boundaries.
- [API Reference](docs/api.md): Available endpoints and examples.
- [Validation Report](docs/validation-report.md): Verified capabilities and open gaps.
