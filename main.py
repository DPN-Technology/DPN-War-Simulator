# Legacy v0.7 3D class is intentionally imported for compatibility/regression visibility.
from warsim.firstperson3d import FirstPerson3DApp
from warsim.seamless3d import SeamlessOpenWorld3DApp

if __name__ == "__main__":
    app = SeamlessOpenWorld3DApp()
    app.mainloop()
