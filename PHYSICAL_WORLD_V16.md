# War Simulator v1.6 — Advanced Physical World & Effects

v1.6 advances the seamless first-person carrier from a dense procedural prototype toward a more physically readable shipboard world. It preserves every v1.5 gameplay system while adding animated structure, environment, weather, visible damage effects, and moving machinery.

## Major additions

- Animated watertight hatches with eased open/close motion around a visible hinge.
- Hatch collision remains tied to the actual operational state while the door model visibly moves.
- Continuous ladder traversal now takes time and moves the camera through the same world coordinate system; ladder rails and individual rungs are rendered.
- Time-of-day lighting changes continuously from night through dawn/day/dusk.
- Training weather presets: Clear, Overcast, Rain, Storm.
- Rain, fog, cloud/sky changes, storm lightning and sea-state-driven exterior presentation.
- Moving radar antenna, engineering ventilation fans and stern propeller visuals.
- Faceted/tapered hull-side geometry below the flight/hangar envelope.
- Visible survivability effects in the actual affected deck zone: fire, smoke, flooding and breach-water effects.
- Weather/environment state is persistent in the career save.
- F7 cycles training weather without stealing any WASD movement key.

## Important accuracy boundary

The v1.6 effects layer is a training/gameplay presentation layer. Exact weather presets, lighting response, hull faceting, animation speeds, particle counts and visual damage placement are not represented as archival USS Enterprise geometry or damage-control-book data unless a later sourced scenario explicitly replaces them.

The existing locked historical Midway timeline and source manifests remain separate.
