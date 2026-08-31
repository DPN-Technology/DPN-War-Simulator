# Software Supply Chain

DPN Technology uses automated supply-chain evidence for this repository.

## Generated Evidence

The `Supply Chain` GitHub Actions workflow generates:

- `SBOM.spdx.json` — SPDX JSON Software Bill of Materials generated from the repository.
- `PROVENANCE.json` — repository, commit, ref, workflow-run, and runner metadata for the build context.
- `SUPPLY_CHAIN_SHA256SUMS.txt` — SHA-256 hashes for the generated evidence files.

The files are uploaded as a GitHub Actions artifact for each successful run.

## Trigger Conditions

Supply-chain validation runs:
- On pushes to `main`
- On pull requests
- Weekly
- On manual dispatch

## Security Intent

This workflow is intended to make dependency and release composition auditable. It does not replace code review, vulnerability management, release testing, or secret scanning.

## Release Integration

The controlled release workflow also produces release-specific provenance and an SPDX SBOM and attaches them to GitHub Releases together with the source archive, release manifest, and checksums.

## Verification

Downloaded evidence can be checked with:

```bash
sha256sum -c SUPPLY_CHAIN_SHA256SUMS.txt
```

Release assets should also be validated against their published `SHA256SUMS.txt`.
