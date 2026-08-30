from warsim.firstperson3d import FirstPerson3DApp, HUB_NODES
from warsim.walkship import EQUIPMENT

app = FirstPerson3DApp()
app.geometry("1280x720")
app.update_idletasks(); app.update()
assert app.world == "HUB"
assert app.overlay == "welcome"
app.overlay = None

# Render actual 3D training facility.
app._render(); app.update_idletasks()
assert len(app.canvas.find_all()) > 25

# Physically approach Academy terminal and open in-world exam overlay.
node = HUB_NODES["ACADEMY"]
app.x, app.y = node.x, node.y
app._interact(); app.update_idletasks()
assert app.overlay == "academy"
app.overlay = None

# Enter bridge via a 3D portal.
node = HUB_NODES["BRIDGE"]
app.world = "HUB"; app.x, app.y = node.x, node.y
app._interact(); app.update_idletasks()
assert app.world == "BRIDGE"
app._render(); app.update_idletasks()

# Enter Enterprise 3D and operate a physical Radio console.
app._enter_world("HUB")
node = HUB_NODES["ENTERPRISE"]
app.x, app.y = node.x, node.y
app._interact(); app.update_idletasks()
assert app.world == "ENTERPRISE"
radio = EQUIPMENT["RADIO_RACK"]
app.shipboard.deck, app.shipboard.x, app.shipboard.y = radio.deck, radio.x, radio.y
app.x, app.y = radio.x, radio.y
app._interact(); app.update_idletasks()
assert app.shipboard.interactions >= 1
app._render(); app.update_idletasks()
assert len(app.canvas.find_all()) > 25

# Confirm 3D historical clock loop advances shared Enterprise state.
before = app.shipboard.enterprise.current_minute
app.running_time = True
app.shipboard.running = True
app.bridge_accum = 0.99
app._update(0.05)
assert app.shipboard.enterprise.current_minute >= before + 1

app.destroyed = True
app.destroy()
print("GUI_SMOKE_V07_PASS")
