# v1.8 Air Combat, Navigation & Pilot Survival

## Purpose
v1.8 turns first-person carrier flight into a persistent operational loop without rewriting the historically locked Midway scenario.

## Cockpit mission state
Each cockpit sortie carries a mission context (CAP, SCOUT, STRIKE, ASW/training). The system can create mission waypoints and training contacts in the same global east/north nautical coordinate space used by Enterprise, the task force, campaign bases and logistics traffic.

## Air-to-air training
- Select a contact with `J`.
- Target markers are drawn into the forward cockpit view.
- `Space` fires a finite gun burst.
- A valid hit depends on range, heading/sight error and altitude separation.
- Ammunition is consumed whether the burst hits or misses.

## Air-to-surface training
- SBD training aircraft carry one bomb.
- TBD training aircraft carry one torpedo.
- `T` releases the carried weapon.
- Bomb and torpedo attacks use different altitude, speed, range and alignment envelopes.
- Surface targets have persistent condition instead of a one-click kill state.

## Navigation and radio
`M` cycles CARRIER / MISSION / HOME BASE navigation. The cockpit displays bearing, range and ETA.

`Q` calls the training task-force radio net. The report provides carrier bearing/range and selected-contact information only to the level currently available to the cockpit layer.

## Aircraft damage
The cockpit aircraft tracks:
- Airframe health
- Engine health
- Control health
- Pilot health

Damage can reduce available power, reduce control effectiveness and eventually stop the engine. Landing feeds remaining aircraft condition and pilot injury back into the persistent Air Group roster.

## Emergency survival
`X` initiates:
- Bailout when altitude is sufficient, or
- Ditching at low altitude.

The aircraft is marked lost in the persistent Air Group. The assigned pilot becomes unavailable while a rescue beacon is active. Search and rescue continues while the wider world simulation runs; a completed rescue restores pilot availability but preserves injuries and aircraft loss.

## Historical boundary
Training contacts, exact weapon envelopes, damage rates, individual aircraft stores, navigation aids and search-and-rescue timing are simulation calibration. They do not replace the locked historical Midway event/report data.
