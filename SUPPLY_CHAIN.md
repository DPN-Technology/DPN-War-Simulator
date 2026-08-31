# Software Supply Chain

DPN Technology uses repository-local automation to preserve release traceability.

## Release Records

Each supported release should include:

- Source archive created from the exact tagged commit
- `SHA256SUMS.txt` for release artifacts
- `RELEASE_MANIFEST.txt` with repository, version, commit, and workflow-run identity
- `SBOM.spdx.json` in SPDX 2.3 JSON format
- `SOURCE_SHA256SUMS.txt` containing SHA-256 hashes for tracked source files
- `DEPENDENCY_INVENTORY.txt` containing declared dependency sources and constraints

## Dependency Sources

The supply-chain generator inventories dependency declarations from supported repository files, including:

- Python `requirements*.txt`
- Node `package.json`
- Gradle/Maven coordinates visible in Gradle build files
- Dockerfile `FROM` images
- GitHub Actions `uses:` references

This is a declared-dependency SBOM. Runtime-loaded plugins, system packages, externally provisioned models, private infrastructure, and software installed outside repository manifests may require additional operational inventory.

## Verification

To verify a source checkout against a release manifest:

```bash
sha256sum -c SOURCE_SHA256SUMS.txt
```

To verify a release ZIP:

```bash
sha256sum -c SHA256SUMS.txt
```

## Release Integrity Rules

- Never overwrite an existing version tag with different source.
- Generate artifacts from the approved tagged commit.
- Do not include production databases, credentials, secrets, logs, or private operational exports in release assets.
- Review dependency changes through CI before merging.
- Keep SBOM and checksum records attached to the same GitHub Release as the source archive.
