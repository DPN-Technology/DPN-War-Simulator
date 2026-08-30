# War Simulator v0.8 — Living Ship Phase

v0.8 includes the phase after seamless traversal: the carrier functions as a place where the player has routine responsibilities, not only combat terminals.

## Player needs

- Hunger
- Hydration
- Fatigue
- Stress
- Wellness

Ignoring severe needs gradually harms routine performance/wellness. Physical mess, berthing and medical interactions restore appropriate values.

## Routine cycle

The living clock starts alongside the Midway watch state. When `R` is active, each real second advances one simulation minute.

NPCs change behavior across watch/mess/off-watch phases. This schedule is deliberately a simulation schedule, not an asserted historical Enterprise watchbill.

## Physical daily-life locations

- Crew mess / galley
- Forward and aft berthing
- Sickbay
- Supply issue room
- Machine shop
- Electrical shop
- Aviation maintenance shop
- Ordnance maintenance shop
- Magazine inspection point
- Damage-control work board

## Maintenance work package

Daily work orders have priority, department, due time, detail, progress and completion state.

Current v0.8 tasks:

1. Magazine temperature/security inspection
2. Electrical distribution/standby inspection
3. Aircraft servicing inspection
4. Machinery preventive-maintenance round
5. Aviation ordnance-area inspection

The player must physically travel to the relevant location and interact there to complete the requirement.

## Career connection

Maintenance completion awards XP and writes to the service log. Completing the entire daily package can award:

`Shipboard Routine & Maintenance`

Open-world time and routine statistics are stored in the career profile.

## Operational interruption

Living-ship activity does not replace historical duty. Midway station tasks use the same running clock, so Radio/CIC/Bridge/Air Ops/Engineering/DC obligations can appear while the player is eating, performing maintenance or moving below decks.
