# DPN War Simulator Roadmap

This roadmap describes the current engineering direction. It is intentionally outcome-based and does not promise fixed delivery dates.

| Horizon | Direction |
| --- | --- |
| **Now** | Increase USS Enterprise realism, modularity, performance, and physical ship-system integration while preserving the Python fallback client. |
| **Next** | Move more traversal, ship interaction, damage, flooding, fire, compartment state, and aircraft operations into the UE5 runtime. |
| **Later** | Unify naval, air, land, logistics, campaign, career, and persistent-world systems inside the modern 3D runtime. |

## Engineering Priorities

- Preserve working behavior while modernizing architecture.
- Add regression coverage before removing compatibility code.
- Keep secrets, live operational data, generated databases, and private keys out of Git.
- Prefer recoverable, observable workflows over silent failure.
- Document production prerequisites separately from development/demo defaults.

## Release Discipline

Each significant release should update:
1. Version metadata.
2. Main README status/version badges.
3. Changelog/release notes.
4. Regression or smoke tests for the changed subsystem.
5. Security/deployment notes when operational behavior changes.
