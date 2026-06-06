import sys
import threading
import keyboard
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QColor, QPixmap
from PyQt6.QtCore import Qt
from window import NookWindow

def make_tray_icon(accent):
    px = QPixmap(16, 16)
    px.fill(QColor(accent))
    return QIcon(px)

def toggle(window):
    if window.isVisible():
        window.hide()
    else:
        window.show()
        window.position_top_right()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = NookWindow()

    # system tray
    tray = QSystemTrayIcon(make_tray_icon(window.accent), app)
    menu = QMenu()
    show_action = menu.addAction("Show Nook")
    quit_action = menu.addAction("Quit")
    show_action.triggered.connect(lambda: toggle(window))
    quit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: toggle(window)
        if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()

    # global hotkey in background thread
    def listen():
        keyboard.add_hotkey("ctrl+shift+space", lambda: toggle(window))
        keyboard.wait()

    t = threading.Thread(target=listen, daemon=True)
    t.start()

    window.show()
    window.position_top_right()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()