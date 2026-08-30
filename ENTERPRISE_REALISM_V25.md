# War Simulator v2.5 — Enterprise Realism & Performance Rebuild

v2.5 pauses feature expansion and rebuilds the carrier/rendering foundation that had become the main quality and performance bottleneck.

## Why this rebuild exists

The pre-v2.5 Enterprise was a 72 x 28 world-unit prototype assembled mostly from one-meter grid tiles and small procedural boxes. The renderer also rebuilt every visible Tk Canvas item every frame. As the project accumulated crew, aircraft, damage, weather, task-force, campaign, ground-war and logistics systems, this produced both high frame cost and a visibly blockout-like ship.

v2.5 does not remove those systems. It changes the carrier scale, visual geometry and hot rendering path underneath them.

## Source-driven dimensions

The rebuild uses a Yorktown-class carrier reference scale rather than the old arbitrary 72-unit hull.

- U.S. Naval History and Heritage Command material lists USS Enterprise (CV-6) at 827 ft 4 in overall length in wartime data.
- Yorktown-class reference data places the flight deck at approximately 244.6 m x 29.9 m and identifies three aircraft elevators.
- The v2.5 seamless ship coordinate footprint is normalized to 245 m x 30 m so one ship world unit is approximately one meter.

This is a scale/proportion correction, not a claim that every v2.5 compartment wall reproduces an archival 1942 general-arrangement drawing.

## Full-scale carrier layout

All six ship levels now use a 245 x 30 coordinate envelope:

- Lower Deck
- Engineering
- Hangar Deck
- Flight Deck
- Island
- Bridge

The ship now includes:

- tapered bow/stern walkable envelope
- long centerline passage structure
- much longer engineering and berthing runs
- approximately 166 m x 19 m hangar envelope inside the carrier footprint
- three physically reachable elevator positions
- concentrated starboard island/bridge structure
- full-length flight-deck movement
- relocated consoles, hatches, campaign/fleet/air-wing stations and damage locations

Existing career saves use one-time coordinate migration and then record `ship_layout_version = 2` so an old on-ship position is not stretched twice.

## Exterior visual rebuild

The carrier exterior is no longer represented only by the old rectangular shell.

The procedural model now adds:

- multiple longitudinal hull stations
- fine bow and tapered stern
- lower hull strake
- upper flare / gallery transition
- long flight-deck overhang
- visible deck-edge fascia
- hangar-side openings and structural columns
- starboard sponsons
- three elevator plates
- full-length centerline markings
- aft arresting-wire set
- chamfered/faceted island tiers
- bridge glazing
- integrated funnel
- tripod-style mast and yards
- director/radar shapes
- four stern propeller representations

Large silhouette surfaces use a separate long-range draw allowance, so the island and deck do not disappear just because the normal close-detail radius is short.

The carrier exterior is also rendered from shore/pier viewpoints instead of only while the player is already aboard.

## Interior visual rebuild

Existing detailed interior systems remain and were rescaled across the full ship:

- Engineering machinery groups and long pipe runs
- Hangar trusses and safety lanes
- Flight-deck railings and deck markings
- Lower-deck berthing and mess furniture
- moving ventilation machinery
- rotating radar
- animated hatches
- damage fire/smoke/flooding effects
- crew and aircraft entities

The physical gameplay map remains grid based for robust collision and pathing, while presentation geometry is increasingly faceted/continuous rather than one visible cube per grid cell.

## Renderer fixes

### 1. Near-plane polygon clipping

Older builds rejected a whole wall/object face if any corner passed behind the near plane. Walking close to a bulkhead could therefore make it pop out of existence. v2.5 clips the polygon against the near plane before projection.

### 2. Merged floor/ceiling spans

The old renderer created a floor polygon and ceiling polygon for every visible one-meter walkable tile. v2.5 combines contiguous cells into long row surfaces.

### 3. Merged bulkhead runs

Continuous exposed wall cells are merged into long north/south/east/west bulkhead surfaces rather than emitted as one wall polygon per grid cell.

### 4. Detail / entity culling

Close decorative geometry and physical entities use smaller configurable radii. Large ship silhouette geometry remains visible independently.

### 5. Reduced procedural tessellation

BALANCED and PERFORMANCE modes reduce cylinder side counts while HIGH retains denser geometry.

### 6. Frame-budgeted main loop

The inherited loop used a fixed post-render delay even when rendering itself was already expensive. v2.5 schedules only the remainder of its target frame budget and can reduce close-detail radii after sustained slow frames in BALANCED mode.

## Visual quality modes

Press `F4`:

- PERFORMANCE — shortest detail/entity distances and lowest procedural tessellation
- BALANCED — default
- HIGH — longer draw/detail distances and denser curved geometry

The default is intentionally optimized for playability. HIGH is available for stronger systems.

## HUD redesign

The v2.4 default HUD covered a large portion of the scene with subsystem telemetry. v2.5 defaults to a compact game HUD showing only:

- location/deck
- view heading and ship heading/speed
- alert state
- quality mode / FPS
- player needs
- current duty/objective
- interaction prompt

Press `TAB` to expand the deep systems/operational picture. This makes the ship, not debug telemetry, the default visual focus.

## Movement scale

Shipboard walking was reduced from the prototype's arcade-fast speed to roughly human-scale movement. Sprint remains available. Shore/battlefield travel retains faster training-world movement so the large combined-arms areas remain practical.

## Internal benchmark

Headless 1280x720/1440-style Tk rendering varies by environment and is not a promise of a specific Windows FPS. In the same project benchmark used during this rebuild, the original dense hangar scene was about 134 ms/frame. The final v2.5 build is approximately 56 ms/frame in that benchmark while rendering the much larger carrier. Flight-deck and Engineering passes are approximately 45 ms and 49 ms respectively.

The benchmark demonstrates a substantial reduction in software-renderer work; actual user hardware and Windows Tk performance will differ.

## Historical boundary

v2.5 improves scale and recognizable Yorktown-class carrier structure. The exact interior partitions, procedural machinery geometry, sponson details, equipment coordinates, flight-deck markings, propeller representation, collision grid and rendering distances remain simulation geometry unless separately sourced.
