import tkinter as tk
from warsim.ui import WarSimulatorApp
from warsim.walkship import move_player

app = WarSimulatorApp()
app.withdraw()
app.update_idletasks()
app.show_shipboard_walkthrough()
app.update_idletasks()
app.update()
assert app.shipboard_state is not None
assert app._screen_name == "USS ENTERPRISE (CV-6) — SHIPBOARD WALKTHROUGH"
# Exercise render/movement/interactions and clock without needing keyboard injection.
for _ in range(6):
    move_player(app.shipboard_state, forward=1)
    app._shipwalk_render()
    app.update_idletasks()
app.shipboard_state.deck = "ISLAND"
app.shipboard_state.x, app.shipboard_state.y = 5.0, 10.0
app._shipwalk_interact()
app._shipwalk_advance(14)
app._shipwalk_render()
app.update_idletasks()
# Open other screens to catch stale key/timer/UI integration problems.
app.show_enterprise_duty(); app.update_idletasks()
app.show_ship_systems(); app.update_idletasks()
app.show_historical_ops(); app.update_idletasks()
app.show_service_record(); app.update_idletasks()
app.destroy()
print("GUI_SMOKE_V05_PASS")
