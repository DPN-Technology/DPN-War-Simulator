# DPN Repository Certification Scorecard

**Repository:** DPN War Simulator  
**Certification baseline:** DPN GitHub Governance v3  
**Reviewed:** 2026-09-01

## Engineering controls

| Control | Status |
| --- | --- |
| DPN repository governance standard | PASS |
| Continuous integration | PASS |
| Cross-platform CI | PASS |
| Runtime assurance | PASS |
| Security gate | PASS |
| Supply-chain workflow | PASS |
| Dependency automation / Dependabot | PASS |
| Release automation | PASS |
| Least-privilege workflow baseline | PASS |
| Immutable SHA-pinned core Actions | PASS |
| Branch/ruleset enforcement | MANUAL VERIFICATION REQUIRED |
| GitHub code scanning / CodeQL entitlement | MANUAL VERIFICATION REQUIRED |
| GitHub secret scanning / push protection | MANUAL VERIFICATION REQUIRED |

## Certification policy

A repository is release-ready only when required simulation, CI, security, runtime, asset-pipeline, supply-chain, and release-integrity checks pass. Historical design documents should be migrated into structured `docs/` areas only after validating references.

## Outstanding governance actions

1. Verify `main` is protected by a ruleset requiring pull requests and required status checks.
2. Verify force-push and branch deletion protections are enabled.
3. Enable GitHub secret scanning and push protection where supported.
4. Enable CodeQL/default setup where supported.
5. Continue safe migration of historical/versioned root documentation after link/reference validation.
