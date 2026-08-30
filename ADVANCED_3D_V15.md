# v1.5 Advanced 3D Environment Pass

v1.5 is the first deliberate pass away from the original block-out visual language. The runtime still uses the project's standard-library perspective renderer, but world objects are now assembled from multiple projected primitives instead of representing almost everything as one rectangular block.

## New environment detail

Interior decks now receive structural framing, overhead utility runs, light fixtures and deck-specific visual systems. Engineering receives large machinery blocks and colored pipe runs; Hangar Deck receives trusses and safety lanes; Flight Deck receives markings, railings/stanchions and mast structure; Lower Deck receives bunks and tables; Island/Bridge spaces receive window banks and denser instrumentation.

## Object models

New procedural model helpers build multi-part:

- Consoles
- Humanoid sailors
- Aircraft
- Surface ships
- Cylindrical masts/pipes/stanchions

This lets the game visually distinguish people, aircraft, ships and equipment instead of displaying them as nearly identical boxes.

## Exterior presentation

Exterior views now include layered atmosphere and animated sea bands. Friendly ships, enemy contacts, logistics groups and carrier aircraft use more readable silhouettes. The ship still uses schematic geometry; the visual upgrade does not claim exact 1942 compartment or hull reconstruction.

## Performance policy

Detail is distance-limited and generated only around the current player position so the single-process Python/Tk renderer remains responsive. The architecture is intentionally compatible with the existing Windows one-file PyInstaller workflow.
