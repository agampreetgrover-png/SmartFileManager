from ui.main_window import MainWindow
from core.app_bridge import AppBridge

app = MainWindow()
app.bridge = AppBridge() # Attach the backend bridge
app.mainloop()