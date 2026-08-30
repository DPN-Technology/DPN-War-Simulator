# War Simulator v1.9 — Expeditionary Ground / Airbase / Amphibious Operations

v1.9 expands the persistent war world ashore while preserving every naval and aviation system from v1.8.

## Seamless shore expansion
The existing Naval Training Base is physically extended south. The player can walk there in the same first-person renderer without loading a separate ground-game scene.

New physical areas:
- Expeditionary Ground Operations Center
- Motor Pool / Vehicle Dispatch
- Expeditionary Airfield Operations
- Training runway/apron
- Amphibious Landing Control
- Expeditionary Supply Staging
- Training Airfield Flight Line

## Ground units
The training state tracks infantry, engineers, air-defense personnel and logistics personnel independently. Each unit has strength, manpower, morale, fatigue, supply, experience, position, current order and status.

## Ground vehicles and logistics
Operational ground vehicles have fuel, health, cargo, crew, position and orders. Supply vehicles can physically advance through the campaign coordinate system and replenish nearby ground units.

The shore motor pool also contains a first-person drivable utility vehicle. It remains inside the same seamless base world and uses collision against the existing walkable geometry.

## Expeditionary airfields
Airfields track runway condition, aviation fuel, ammunition, repair stores, medical stores and security. Servicing an airfield transfers finite stores from the supporting naval campaign base rather than creating unlimited supplies.

## Amphibious operations
The first amphibious training group can launch toward a training beachhead, move through the operational coordinate system, land an embarked force and establish a beachhead. This is a training framework, not a claim about a specific historical landing.

## Ground missions
v1.9 includes four persistent training operations:
- Forward Airfield Defense
- Amphibious Landing Exercise Alpha
- Forward Ground Supply Route
- Reconnaissance Patrol Sector Red

Missions require physical unit presence and, where applicable, air support or an amphibious beachhead. They progress over operational time instead of completing instantly.

## Carrier air integration
Completed Air Group missions contribute limited abstract air-support points to ground operations. Ground missions do not receive hidden historical information or perfect battlefield awareness.

## Rank / chain-of-command integration
Ground commands are rank-gated. Junior personnel can inspect the board and report; higher authority is required to accept operations, dispatch forces or order an amphibious landing.

## Training-data boundary
The exact manpower, unit names, vehicles, airfield locations, stock quantities, landing geometry, mission timing and ground-movement coefficients are explicitly training abstractions. The locked Midway historical scenario remains unchanged.
