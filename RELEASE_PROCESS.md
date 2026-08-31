# DPN Technology Release Process

This document defines the minimum release discipline for **DPN-War-Simulator**.

## 1. Prepare the Release

Before declaring a release:
1. Confirm the target changes are merged into the intended release branch.
2. Update every application-visible version location that applies to the project.
3. Update `README.md` release/version information.
4. Update `CHANGELOG.md` or the project's versioned release notes.
5. Update architecture, deployment, migration, security, and recovery documentation when behavior changed.
6. Confirm no live credentials, databases, backups, private keys, runtime state, or private exports are tracked.

## 2. Validate

Required:
- Main CI workflow passes.
- Relevant regression/smoke tests pass.
- Installer/startup path is tested when applicable.
- Upgrade/migration path is tested when applicable.
- Backup/recovery or rollback impact is reviewed.
- Security/permission changes receive explicit review.
- User-facing version information is consistent.

A release should not be marked complete while the current `main` CI badge is red.

## 3. Release Candidate

For higher-risk releases, create a release candidate branch or tag first:

```bash
git checkout -b release/<version>
git push -u origin release/<version>
```

Run production-like validation using non-production data and secrets.

## 4. Tag the Approved Commit

After validation:

```bash
git checkout main
git pull --ff-only
git tag -a <version> -m "DPN-War-Simulator <version>"
git push origin <version>
```

Use the project's established version style, such as `v5.0.7`, `v18.42`, or another documented format.

## 5. GitHub Release

Create a GitHub Release from the approved tag and include:
- Version
- Release date
- Major features
- Fixes
- Security changes
- Breaking changes
- Migration/upgrade steps
- Known limitations
- Rollback/recovery notes

Attach only approved distributable artifacts. Never attach production databases, credentials, private logs, keys, or private customer/employee data.

## 6. Build Artifacts

Where applicable, release artifacts should be generated from the tagged source rather than an uncommitted local working copy.

Recommended artifact metadata:
- File name
- Application version
- Build date
- Platform/architecture
- SHA-256 checksum

Example:

```bash
sha256sum <artifact>
```

## 7. Post-Release Verification

After release:
1. Install/start the released build in a clean environment when practical.
2. Confirm the version displayed by the application.
3. Run a basic operational smoke test.
4. Confirm backup/recovery behavior.
5. Confirm the README CI badge remains green.
6. Record any immediate regression as a GitHub issue.

## 8. Hotfixes

Hotfixes should:
1. Reproduce the production defect.
2. Add regression coverage where possible.
3. Make the smallest safe correction.
4. Pass CI.
5. Increment version metadata.
6. Update changelog/release notes.
7. Tag and publish a new release rather than silently replacing an existing tagged release.

## 9. Rollback

Never delete or rewrite an already distributed release merely to hide a defect. Preserve history, document the issue, and issue a corrected release.

If rollback is required, use the last known-good tagged release and follow the project's documented data/recovery procedures.
