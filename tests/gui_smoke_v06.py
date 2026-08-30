import tkinter as tk
from warsim.ui import WarSimulatorApp
from warsim.walkship import move_player, update_crew_movement, HATCHES

app = WarSimulatorApp()
app.withdraw()
app.update_idletasks()
app.show_shipboard_walkthrough()
app.update_idletasks(); app.update()
assert app.shipboard_state is not None
st = app.shipboard_state
assert app._screen_name == "USS ENTERPRISE (CV-6) — SHIPBOARD WALKTHROUGH"
# Move/render and animate NPCs.
for _ in range(6):
    move_player(st, forward=1)
    update_crew_movement(st, 0.1)
    app._shipwalk_render(); app.update_idletasks()
# Operate a hatch physically.
h = HATCHES["ISLAND_PORT"]
st.deck, st.x, st.y = h.deck, h.x, h.y - 0.3
app._shipwalk_interact(); app.update_idletasks()
assert st.hatches[h.key] is False
# Complete priority radio task physically.
st.deck, st.x, st.y = "ISLAND", 5.0, 10.0
app._shipwalk_interact(); app.update_idletasks()
# Advance to first training inject and restore it.
app._shipwalk_advance(165)
st.deck, st.x, st.y = "ISLAND", 10.5, 14.0
app._shipwalk_interact(); app.update_idletasks()
assert st.training_faults_resolved >= 1
# Verify added UI tabs/text widgets exist and can render.
app._shipwalk_render(); app.update_idletasks()
assert hasattr(app, "_sw_systems_text") and hasattr(app, "_sw_crew_text")
# Open older screens to catch integration regressions.
app.show_enterprise_duty(); app.update_idletasks()
app.show_ship_systems(); app.update_idletasks()
app.show_historical_ops(); app.update_idletasks()
app.show_service_record(); app.update_idletasks()
app.destroy()
print("GUI_SMOKE_V06_PASS")
