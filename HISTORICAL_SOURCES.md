# v1.0 Historical / Combat Accuracy Note

v1.0 does not add a new claimed historical Enterprise casualty or rewrite the Battle of Midway timeline.

The existing Midway/Enterprise source registry from earlier builds remains the historical basis for the locked scenario. The v1.0 live combat problem is explicitly labeled a **SIMULATED RAID** and exists to exercise reusable combat mechanics.

The following v1.0 values are simulation calibration unless a future scenario replaces them with source-specific data:

- Weapon engagement ranges/effectiveness
- Ready-service and reserve ammunition quantities
- Training raid contact geometry and behavior
- Damage severity values
- Aviation fuel/ammunition/bomb/torpedo resource pools
- CAP interception rates

Enterprise interior geometry also remains a training schematic rather than an exact 1942 deck plan.

See the earlier historical source material in the project for the Battle of Midway / USS Enterprise historical layer. See `historical_data/naval_combat_v10.json` for the explicit separation policy.

## v1.2 command/crew note
v1.2 does not add a new historical-event source. It continues using the existing sourced Midway/Enterprise historical layer. The new department-head names, authority tiers, manpower counts, watch-relief timing, supply quantities and autonomous-response rates are explicitly simulation/training abstractions and are not presented as an exact June 1942 USS Enterprise watchbill.

## v1.3 Task Force Operations

v1.3 reuses the existing sourced Task Force 16 order-of-battle entries in `historical_data/midway_1942_manifest.json` for friendly ship names. It does not add new historical claims for exact formation spacing, AI captain behavior, sensor performance, fuel/ammunition quantities, underway replenishment rates, or hostile surface/submarine contacts. Those are explicitly simulation/training abstractions recorded in `historical_data/task_force_v13.json`.

## v1.4 Persistent Campaign

v1.4 adds no new claim that its operational bases, coordinates, stock quantities, convoy schedules, repair capacities, threat-zone geometry or campaign missions reproduce an exact historical 1942 logistics network. Those features are explicitly recorded as training abstractions in `historical_data/campaign_v14.json`. The existing sourced Battle of Midway historical timeline and TF16 unit-name data remain separate and unchanged.

## v1.5 Carrier Air Group verification

For v1.5, the squadron labels and aircraft families used by the persistent Air Group were checked against U.S. Naval History and Heritage Command material. NHHC's Enterprise ship history describes Enterprise launching F4F Wildcats of VF-6, SBD Dauntlesses of VB-6 and VS-6, and TBD Devastators of VT-6 during the Battle of Midway. NHHC also preserves the Bombing Squadron Six action report and the Enterprise action report.

Sources:
- NHHC, *Enterprise VII (CV-6)*: https://www.history.navy.mil/research/histories/ship-histories/danfs/e/enterprise-cv-6-vii.html
- NHHC, *USS Enterprise (CV-6) Action Report — Battle of Midway*: https://www.history.navy.mil/content/history/nhhc/research/archives/digital-exhibits-highlights/action-reports/wwii-battle-of-midway/uss-enterprise-action-report.html
- NHHC, *Bombing Squadron 6 (VB-6) Action Report*: https://www.history.navy.mil/research/archives/digital-exhibits-highlights/action-reports/wwii-battle-of-midway/bombing-squadron-6.html
- NHHC, *Battle of Midway*: https://www.history.navy.mil/browse-by-topic/wars-conflicts-and-operations/world-war-ii/1942/midway.html

Historical safeguard: v1.5 verifies the squadron labels/aircraft families, but **does not claim** its exact individual aircrew names, roster sizes, aircraft condition, stores, mission ranges, sortie rates or training mission results are exact June 1942 records. Those remain training abstractions.

## v1.7 presentation/flight boundary
v1.7 inherits the sourced Enterprise/Midway and Air Group identity material already registered in earlier phases. It does **not** add claims that the new cockpit handling coefficients, takeoff/recovery envelope, fuel burn, procedural crew animation, expanded doorway locations, electrical arc/steam effects, or cockpit geometry reproduce archival CV-6/F4F/SBD/TBD measurements. Those are training/gameplay abstractions recorded in `historical_data/flight_world_v17.json`.

## v1.8 Air combat / navigation / survival boundary
v1.8 inherits the previously registered Enterprise/Midway and VF-6/VB-6/VS-6/VT-6 aircraft-family material. It adds no claim that its training opponents, gun ammunition quantities, firing envelopes, bomb/torpedo release envelopes, aircraft damage coefficients, navigation aids, pilot injury thresholds, bailout/ditching criteria, or search-and-rescue timing reproduce exact June 1942 combat data. Those values are explicitly recorded as training/gameplay abstractions in `historical_data/flight_combat_v18.json`.


## v1.9 Expeditionary ground / airbase / amphibious boundary
v1.9 expands the simulation into shore and ground operations but does not claim a sourced historical ground order of battle. The exact ground-unit names, manpower, vehicle performance, expeditionary airfield coordinates/stocks, Training Island Alpha geography, amphibious-craft performance, ground-mission timing, air-support point model and ground logistics rates are explicitly training/gameplay abstractions. They are registered in `historical_data/ground_ops_v19.json`. The previously sourced and locked Battle of Midway historical layer remains unchanged.

## v2.0 Combined-Arms Ground Combat

v2.0 does not add a new claimed historical battle. The combined-arms training village, fireteam/opposing-force roster, weapon performance, support effects and casualty coefficients are explicitly training/gameplay abstractions. The existing locked historical Midway scenario remains unchanged.

## v2.2 Strategic-war separation

v2.2 does not add a new historical battle dataset. Its theater sectors, formation names/sizes, commander names, depots, routes, bridge states, reinforcement timing and enemy operational AI are explicitly training/gameplay abstractions. They are stored in `historical_data/strategic_war_v22.json` so they cannot be confused with the sourced Midway historical layer.

## v2.3 National war-economy separation
v2.3 does not add a historical national-production dataset. Factory names/coordinates, stockpile quantities, resource costs, production rates, research effects, training throughput, transport capacity and industrial interdiction are explicitly training/gameplay abstractions. They are registered in `historical_data/war_economy_v23.json` and remain separate from the sourced Midway historical layer.

## v2.4 Strategic-mobility separation
v2.4 adds no new claimed historical logistics network. The National Distribution Depot, Strategic Port Delta, Railhead Echo, Forward Depot Foxtrot, Air Logistics Hub Golf, Fleet Anchorage Hotel, route distances/speeds/capacities, cargo package quantities, escort effects and interdiction coefficients are explicitly training/gameplay abstractions. They are registered in `historical_data/logistics_v24.json` and remain separate from the sourced/locked Midway historical layer.

## v2.5 Enterprise scale / visual reference boundary

v2.5 uses source material to correct the gross scale/proportions of the playable carrier rather than continuing the old 72-unit prototype.

Source-supported reference points used by the rebuild:
- U.S. Naval History and Heritage Command / USS Enterprise (CV-6) wartime data lists an overall length of 827 ft 4 in.
- Yorktown-class reference material lists a flight deck of approximately 244.6 m x 29.9 m, a hangar approximately 166.4 m x 19.2 m, and three aircraft elevators.

The v2.5 gameplay coordinate footprint is normalized to 245 m x 30 m using the flight-deck reference. This is not a claim that its exact collision grid, interior compartment partitions, machinery shapes, island dimensions, sponson locations, bridge-window spacing, arresting-wire positions or equipment coordinates duplicate a specific 1942 general-arrangement plan. Those remain procedural/training geometry.

Reference URLs retained for project traceability:
- NHHC USS Enterprise (CV-6) ship history / wartime dimensions: https://www.history.navy.mil/research/histories/ship-histories/danfs/e/enterprise-cv-6-vii.html
- Yorktown-class carrier dimensional reference: https://www.navypedia.org/ships/usa/us_cv_yorktown.htm

## v2.6 Midway 1942 Enterprise visual target

The visual target is Enterprise in late May / early June 1942 around Midway. The model uses period-photo evidence for visible features such as the wooden flight deck, metal tie-down strips and distance markings; the island's large stack, masthead CXAM-1 radar, searchlights and aircraft crane; and the period close-range AA battery.

The implementation keeps a strict reconstruction boundary. Exact hull station curves, island measurements, gun coordinates, camouflage RGB values, internal partitions and representative aircraft parking remain reconstruction/game-art approximations until suitable archival drawings are traced. See `historical_data/enterprise_1942_visual_v26.json`.

## v2.7 Enterprise CV-6 Midway reconstruction source boundary
v2.7 remains locked to late May / early June 1942. The exterior art pass uses official Navy/NHHC March–June 1942 Enterprise imagery for visible island/mast/radar/crane/director/weapon cues and a 1940 Yorktown-class CV-5 Booklet of General Plans as a class-level arrangement reference. The source manifest is `historical_data/enterprise_1942_reconstruction_v27.json`.

Key period reference identifiers used by the reconstruction include NHHC 19-N-29691 (forward/island view), NHHC 19-N-29697 (aft-island/crane/director view), NHHC 80-G-32225 (Enterprise at sea during Midway), and the NHHC DANFS Enterprise CV-6 history for March 1942 alterations and the 20 mm fit. The Maritime Park Association plan index confirms the 1940 Yorktown-class CV-5 Booklet of General Plans.

The following remain explicitly reconstruction-only until Enterprise-specific archival drawings are traced: hidden compartment partitions, exact machinery arrangements, exact CIC/bridge equipment coordinates, exact hull plate seams, exact gun/fitting coordinates, and exact paint/PBR values.
