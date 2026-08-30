# War Simulator v2.3 — National War Economy & Industrial Production

v2.3 adds a persistent national production layer above v2.2 strategic war. It is a training/gameplay abstraction, not a historical national-production dataset.

## Industrial facilities
- Central Aircraft Works
- Armored Vehicle Plant
- National Munitions Complex
- Fleet Shipyard & Repair Basin
- Strategic Fuel Refinery
- National Training Command
- Rail / Port Logistics Directorate

Each facility tracks effective capacity, efficiency, damage, power, workforce, maintenance, queue assignment, and cumulative output. Damage and transport disruption reduce production instead of only changing a text status.

## Raw reserves and stockpiles
Production consumes steel, aluminum, oil, explosives, and food. Finished national stockpiles include fighter/attack airframes, tanks, trucks, naval ammunition, artillery shells, small-arms ammunition, repair stores, aviation fuel, bunker fuel, medical stores, and trained replacement personnel.

## Production orders
Production orders advance over operational time, consume raw materials per finished unit, can pause on material shortage, and deposit completed equipment into national stockpiles. A facility kind can only run one selected production priority at a time.

## Research and training
Research programs improve production, logistics, repair, or training efficiency. Training pipelines graduate general replacements, pilots, and technical personnel into the national replacement pool.

## Transport network
Rail, road, port, and merchant-shipping capacity form a national throughput value. Damage reduces the rate at which factories receive materials and strategic allocations can move. Repair consumes national repair stores.

## Long-war consequences
When the war-economy layer is active, friendly strategic reinforcement waves require trained personnel, ammunition, and fuel. Shortages delay reinforcement arrival. National stocks can be allocated to:
- THEATER — strategic depots and replacement pools
- NAVY — task-force fuel, ammunition, and repair stores
- AIR — Carrier Air Group replacement airframe, fuel, and spares
- LAND — armored replacement, artillery ammunition, and trained personnel
- BASES — campaign-base fuel, aviation fuel, medical, and repair stocks

## Physical world
The same seamless shore coordinate system now continues into an industrial district south of Theater Command. The aircraft works, armor plant, munitions complex, shipyard, refinery, training command, and rail/port control are all physically reachable without a loading screen.

## Controls
Press F12 or physically use the National War Production Board.
- TAB facility
- O production order
- R research project
- T training pipeline
- D allocation destination (only while the economy board is open)
- S start national war economy
- P activate selected production order
- I start selected research
- G start/pause selected training pipeline
- F repair selected factory
- X repair transport network
- A allocate national stocks
- F12 / E / Esc close

Normal first-person `D` remains right-strafe only.
