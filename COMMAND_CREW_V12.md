# War Simulator v1.2 — Command, Crew & Autonomous Ship Operations

## Purpose
v1.2 makes the ship operate around the player instead of waiting for the player to press every button. The system models a training-oriented chain of command, department readiness, rank-gated authority, watch reliefs, autonomous emergency response, accountability, logistics consumption, and persistent command performance.

## Rank-gated authority
Authority is intentionally progressive. Recruits and junior enlisted can perform work and submit reports through the chain of command. Petty officers/chiefs can prioritize team work. Warrant/junior officers gain division/department authority. Senior officers gain ship-command authority. Exact thresholds are gameplay training abstractions, not an archival claim about every historical billet.

## Departments
The command model tracks Bridge/Navigation, CIC, Radio, Engineering, Damage Control, Fire Control/Air Defense, Aviation Operations, Medical, and Supply/Logistics. Each has manpower, available personnel, readiness, fatigue, morale, a department head, an active order, response progress, and response history.

The named department heads in this build are simulation roster placeholders. They are not presented as the exact June 1942 USS Enterprise watchbill.

## Orders
The physical Bridge command desk and the C shortcut expose command status. Available orders include condition reports, casualty repair priority, watertight integrity, casualty receiving, engineering restoration, air-defense readiness, aviation readiness, General Quarters, accountability muster, supply replenishment, and stand-down.

Orders have priority, department, issue time, deadline, progress, completion/failure state, source, and minimum authority. Orders do not resolve instantly.

## Autonomous response
Combat alarms can automatically set General Quarters. Structural damage can automatically dispatch Damage Control and Medical teams. Propulsion/steering degradation can generate Engineering restoration orders. Department response speed depends on readiness, morale, fatigue, manpower, and supplies.

Damage Control gradually attacks fire/flooding and structural damage while consuming firefighting agent and repair material. Medical teams gradually treat wounded while consuming medical stores. Engineering teams restore maneuvering integrity while consuming electrical spares.

## Living crew integration
Visible NPC watchstanders route to battle stations or ordered duties in the same seamless 3D world. The player can continue moving through the ship while crew response is underway.

## Watches and logistics
The ship changes watch sections on a four-hour training cycle when not at General Quarters. Relief reduces department fatigue. Provisions and fresh water are consumed continuously. Repair material, medical supplies, electrical spares, firefighting agent, and replacement-personnel reserve are finite command resources.

## Persistence
Command condition, watch section, department readiness, orders, supplies, casualty accounting, autonomous actions, and command score are saved with the career. Older v1.1 and earlier career files remain compatible.
