# Development Workflow

**Project:** VLAI LLM Serving  
**Audience:** Backend, infrastructure, and AI engineers  
**Status:** Team development process. Production deployment is not yet implemented.

This document defines how code moves from an individual developer's branch into the shared codebase. Read [CONTRIBUTING.md](../CONTRIBUTING.md) first for local setup commands.

## 1. Branch strategy

We use a lightweight two-branch workflow:

```text
feat/*  fix/*  test/*  docs/*  chore/*
             |  Pull Request + CI + review
             v
          develop
             |  Release PR + validation
             v
           main
             |  Approved tag + deployment procedure
             v
       Production (future)

hotfix/* (from main) -> PR to main -> sync fix back to develop
```

| Branch | Role | How changes enter |
| --- | --- | --- |
| `main` | Approved, release-ready source; **not proof of a live deployment** | Release PR from `develop` or an urgent hotfix PR |
| `develop` | Integration branch for ongoing development | PR from a short-lived topic branch |
| `feat/*` | New feature | Branch from `develop` |
| `fix/*` | Bug fix before release | Branch from `develop` |
| `test/*`, `docs/*`, `chore/*` | Tests, docs, maintenance | Branch from `develop` |
| `hotfix/*` | Urgent fix for a released version | Branch from `main`; bring fix back to `develop` |

Keep `main` and `develop` protected: no normal direct pushes, no force pushes, and no deletion. Changes must pass configured PR checks. Review approval requirements are enforced by the current repository ruleset; the PR author cannot satisfy their own approval requirement.

## 2. Daily developer workflow

Start from a GitHub Issue when possible. Before creating a new branch, ensure your worktree is clean:

```bash
git status
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c feat/short-description
```

Make incremental commits. Use short Conventional Commit-style messages such as:

```text
feat: add API key authentication
fix: close disconnected streaming clients
test: cover upstream timeout handling
docs: explain API configuration
chore: update CI workflow
```

Before creating a PR:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check src tests
```

Push the branch and open a PR to **`develop`**, not `main`. Describe why the change is needed, what was changed, what was tested, compatibility implications, and related Issues. Prefer small PRs so reviewers can understand each change.

## 3. Pull requests and code review

**Author responsibilities**

1. Fill in the PR template and request a reviewer if required.
2. Confirm the CI status is green; investigate failures rather than bypassing checks.
3. Respond to inline comments, update tests and docs, and push fixes to the same branch.
4. Do not merge until GitHub reports that all required checks and approvals have passed.

**Reviewer responsibilities**

1. Open **Files changed** and examine the implementation and tests.
2. Review correctness, security, error handling, compatibility, and maintenance impact.
3. Choose **Comment** for suggestions, **Request changes** for blocking issues, or **Approve** once ready.
4. Re-review if code changes invalidate the previous approval or the ruleset asks for another review.

A written comment such as `ready` is **not** an approval. Required approvals must be submitted using GitHub's review interface by a collaborator whose permissions meet the configured rule. Contributors may not approve their own PRs to satisfy that requirement.

For regular topic PRs, prefer **Squash and merge** into `develop`, then remove the branch. Merge `develop` into `main` through a separate release PR after release validation. The team may retain a merge commit for release PRs to preserve ancestry.

## 4. Continuous Integration

The `.github/workflows/ci.yml` workflow is designed to run on PRs targeting `develop` or `main`, and on pushes to those branches. Its job is named `backend-checks`.

| Check | Command | Goal |
| --- | --- | --- |
| Unit/integration tests (mock vLLM) | `python -m pytest -q` | Catch backend regressions |
| Lint | `python -m ruff check .` | Check Python lint rules |
| Formatting | `python -m ruff format --check src tests` | Check code formatting |

CI does **not** run a GPU inference server. The current tests use `httpx.MockTransport`; they do not verify a real vLLM process, streaming timing, OpenCode integration, auth, or production deployment. Changes to model configuration, streaming, parser behavior, or inference performance need additional GPU-based validation recorded in the PR.

The repository owner should configure `backend-checks` as a required status check for both protected branches once it has run successfully. If required checks fail or are pending, do not bypass them to merge.

## 5. Release process

A release is a reviewed code baseline, not automatically a deployed service.

1. Select the intended changes from `develop` and confirm all related PRs and tests are complete.
2. Perform additional live FastAPI-to-vLLM checks on an approved GPU host when relevant: model discovery, normal chat, SSE streaming, and tool calls. Record observed results, not assumptions.
3. Open a PR from **`develop` into `main`**. Review the full release diff and operational impact.
4. Merge after required checks and approvals pass.
5. Create an annotated version tag from the release commit, for example `v0.1.0` (example only).
6. Deploy only through an approved, documented procedure when production deployment infrastructure is ready. Verify readiness and error/latency metrics after deployment.

For reproducibility, record the exact Git commit, Docker image digest, model checkpoint revision, dependency versions, and inference configuration. The current development startup references a Docker tag and a model repository without immutable pinning; do not claim reproducible production releases until these are pinned and tested.

**Do not assume a Git tag or a merge to `main` will deploy anything automatically.** The repository's current documented execution model is a manual local setup.

## 6. Hotfix and rollback

For an urgent issue in a released version:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c hotfix/short-description
```

Implement the minimal fix, add regression tests, and open a PR to **`main`**. Once approved and verified, create a new patch release, then **synchronize the fix back to `develop`** through a PR (or a reviewed cherry-pick if histories conflict).

Rollback means redeploying a previously verified application artifact and its compatible model/runtime configuration. Do not use a forced Git history rewrite as a substitute for operational rollback. The actual rollback procedure must be validated before public production use.

## 7. AI-serving-specific review checklist

When reviewing API or inference changes, consider:

- **API compatibility:** `/health`, `/v1/models`, and `/v1/chat/completions` response behavior remains consistent.
- **Streaming:** SSE chunks, `[DONE]` termination, client cancellation, and streamed tool-call arguments are handled safely.
- **Errors:** Upstream connection failures and timeouts are translated predictably; tests cover error paths.
- **GPU/runtime:** Model ID, context size, memory target, parser configuration, and Docker/runtime revisions are documented when changed.
- **Security:** Secrets are never committed; input, output, logging, and access boundaries are reviewed. Do not expose the API publicly without authentication, HTTPS, rate limiting, and authorization controls.
- **Performance:** Resource or latency claims require reproducible measurements, not just successful unit tests.

## 8. Ownership and documentation

The PR author owns implementation and initial testing. A reviewer owns independent technical review, not the author's code. The maintainer controls release approvals and infrastructure access. Avoid granting GPU-host SSH access just to run standard mocked tests.

Keep these files up to date when the workflow changes:

- [CONTRIBUTING.md](../CONTRIBUTING.md): New-developer quick start.
- [README.md](../README.md): Project entry point.
- [Architecture](architecture.md) and [API Reference](api.md): Runtime and interface behavior.
- [Deployment Guide](deployment.md), [Migration Guide](migration.md), and [Validation Report](validation-report.md): Operational procedures and evidence.

**Note:** Branch protection and required approvals are controlled by GitHub settings, not by this Markdown file. If documentation and active rulesets differ, verify settings with the repository maintainer and update the docs.
