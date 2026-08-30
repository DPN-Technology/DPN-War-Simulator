# War Simulator v2.1 — Large-Scale Land Warfare & Battlefield Command

v2.1 expands the seamless combined-arms world south of the v2.0 training village into a battalion-scale maneuver area. It is a **training/gameplay simulation layer**; exact unit names, force sizes, vehicle performance, artillery effects, battlefield geometry and opposition are not represented as historical facts.

## Seamless battlefield

The shore-base map now continues into Battalion/Platoon Tactical Command, Armored Vehicle Staging, Artillery Fire Direction Center, Field Hospital/CASEVAC, Battalion Logistics, Engineer/Vehicle Maintenance and four large battlefield sectors. No scene load occurs between the original naval base, expeditionary district, infantry village and v2.1 maneuver area.

## Battalion command

The battlefield tracks six friendly formations: two rifle platoons, a weapons platoon, combat engineers, medical personnel and combat logistics. Every formation has manpower, casualties, wounded, morale, suppression, ammunition, readiness, fatigue, experience, order, target position and live battlefield position.

Orders include HOLD, ADVANCE, SUPPRESS, ASSAULT, DIG IN, WITHDRAW and RESUPPLY. Orders remain rank/authority gated through the existing chain-of-command model.

## Battlefield sectors

Four sectors track friendly control, enemy strength, fortification and status. Units physically move to the selected sector and sector control changes over time according to friendly combat power, enemy resistance, suppression, readiness and supplies.

## Armored and support vehicles

The training roster includes medium tanks, an armored troop carrier, a logistics truck and field ambulance. Vehicles track position, heading, speed, throttle, fuel, hull, mobility, crew and finite ammunition.

At Armored Vehicle Staging, press E to enter the nearest serviceable vehicle. Direct controls are I engine, W/S throttle, A/D steering, B brake, SPACE fire, T target and E dismount while stopped. **D only steers right in this mode and never opens Damage Control.**

## Artillery and joint fires

Field Artillery Battery A has finite shells and a cooldown between fire missions. Carrier/airfield support consumes ground_ops air-support points. Naval gunfire consumes ammunition from a serviceable task-force escort. These effects are game abstractions rather than historical firing tables.

## Logistics and medical response

Battalion ammunition, fuel, rations, medical stores and repair parts are finite. Resupply consumes stocks. CASEVAC moves wounded personnel to the field hospital over time rather than instantly removing casualties. Vehicle maintenance consumes repair parts and fuel.

## Persistence

The entire v2.1 state is saved in `land_warfare_snapshot`, including units, casualties, sectors, contacts, vehicles, ammunition, logistics, artillery, CASEVAC and operation progress. Older saves load with a default v2.1 state.
