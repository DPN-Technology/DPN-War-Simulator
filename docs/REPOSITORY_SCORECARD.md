# DPN Repository Certification Scorecard

**Repository:** DPN War Simulator  
**Certification baseline:** DPN GitHub Governance v4  
**Reviewed:** 2026-09-01  
**Baseline commit:** `5b5ea077c88d4b1484cde17415e7c354981e255f`  
**Certification:** CONDITIONAL — automated engineering controls healthy; settings enforcement requires external verification.

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
| Branch/ruleset enforcement | BLOCKED BY INTEGRATION / PLAN |
| GitHub code scanning / CodeQL entitlement | MANUAL VERIFICATION REQUIRED |
| GitHub secret scanning / push protection | MANUAL VERIFICATION REQUIRED |

## Governance v4 certification

The audited v3 baseline CI and security activity completed successfully. No Critical repository-file defect was confirmed. Historical/versioned design material remains intentionally unmoved until inbound links and tooling references can be validated.

## Certification policy

A repository is release-ready only when required simulation, CI, security, runtime, asset-pipeline, supply-chain, packaging, and release-integrity checks pass.

## Outstanding governance actions

1. Enforce protected `main` with pull requests and required status checks when account permissions/plan allow it.
2. Block force pushes and branch deletion except documented emergency bypass.
3. Verify secret scanning and push protection support.
4. Verify CodeQL/default setup for supported languages.
5. Continue safe migration of historical/versioned root documentation only after reference validation.
