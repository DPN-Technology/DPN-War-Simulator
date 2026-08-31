# Contributing to DPN War Simulator

War Simulator is an active DPN Technology simulation project. Changes should preserve the separation between playable simulation logic, historical source material, reconstruction assumptions, and the Unreal Engine migration.

## Preferred Workflow

1. Branch from `main`.
2. Make a focused change.
3. Add/update tests for changed simulation behavior.
4. Run the Python test suite.
5. Update version/design documentation when behavior changes.
6. Open a pull request and complete the checklist.
7. Merge after CI passes.

## Local Validation

Install test tooling:

```bash
python -m pip install pytest
```

Run:

```bash
pytest -q tests
```

The version-specific GUI smoke scripts are additional manual/regression checks and are not the primary headless CI target.

## Unreal Engine Changes

The repository contains UE5 source and project scaffolding, but CI does not claim to compile/cook Unreal Engine without an installed UE environment. UE changes should be validated locally with the documented UE5 workflow.

## Historical Claims

Do not present gameplay values, provisional interiors, economy coefficients, or reconstruction assumptions as archival facts. Update the historical/reconstruction documentation when new evidence changes an assumption.

## Security

Follow `SECURITY.md` and do not commit secrets or unlicensed third-party content.
