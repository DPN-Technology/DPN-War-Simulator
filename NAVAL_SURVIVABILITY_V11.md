# War Simulator v1.1 — Structural Damage & Survivability

v1.1 replaces single-number combat damage with a persistent ship-survivability layer.

## Localized damage zones
The training carrier is divided into structural zones spanning the flight deck, island, hangar,
machinery spaces, lower hull, magazines, sickbay and steering gear. Each zone tracks structural
condition, fire, smoke, flooding, breach area, temperature, oxygen and casualties.

## Impact model
Reusable combat hits can create penetration/blast damage, structural degradation, fires,
smoke, hull breaches, flooding, casualties and magazine risk. Torpedo, bomb and shell-style
training impacts produce different casualty patterns.

## Progressive casualties
Damage continues evolving after impact. Hull breaches admit water until patched; pumps remove
water only while available; fire produces heat/smoke and can spread; smoke/flooding/fire can
move through open or failed boundaries. Watertight isolation materially changes propagation.

## Stability and buoyancy
The model derives total flooding, port/starboard list, bow/stern trim, buoyancy, stability and
structural-strength margins from the live compartment state. Large asymmetric floods create list;
fore/aft flooding creates trim. Critical loss of buoyancy, stability or structure enters a sinking
state.

## Operational consequences
Machinery-space damage reduces propulsion capability. Steering-space damage reduces steering.
Island damage reduces combat capability. Flight/hangar damage reduces aviation capability. These
factors feed back into the existing moving-ship/naval-combat runtime.

## Damage-control actions
At Damage Control Central the player can select casualty spaces, fight fires, rig dewatering,
patch breaches, shore weakened structure and control ventilation. The physical boundary board
operates watertight boundaries. Sickbay handles wounded personnel.

## Magazine danger
Magazine spaces accumulate danger from heat, fire and structural damage. Extreme magazine risk
can produce catastrophic structural failure in the training model.

## Abandon ship
If a vessel becomes unrecoverable, the player can order abandon ship. Evacuation then progresses
over time and can be accelerated by physically reporting to the Hangar Deck survival-gear/muster
station. Sinking is a state, not an instant game-over flag.

## Historical-data policy
All structural coefficients are training calibration. This module does not claim exact CV-6 armor,
compartment, weapon-penetration or casualty data. The Battle of Midway historical layer remains
separate and locked.
