# Software Supply Chain

DPN Technology preserves release traceability with repository-local automation.

Each supported release should include:
- Source archive from the exact tagged commit
- `SHA256SUMS.txt`
- `RELEASE_MANIFEST.txt`
- `SBOM.spdx.json` (SPDX 2.3 JSON)
- `SOURCE_SHA256SUMS.txt`
- `DEPENDENCY_INVENTORY.txt`

The inventory discovers declared dependencies from Python requirements files, Node package manifests, Gradle/Maven coordinates, Docker base images, and GitHub Actions references.

This is a declared-dependency SBOM. Runtime plugins, operating-system packages, externally installed models, and infrastructure not declared in the repository may require separate operational inventory.

Verify tracked source with:

```bash
sha256sum -c SOURCE_SHA256SUMS.txt
```

Verify release artifacts with:

```bash
sha256sum -c SHA256SUMS.txt
```

Never overwrite an existing version tag with different source, and never include production credentials, databases, backups, private logs, or private operational exports in release assets.
