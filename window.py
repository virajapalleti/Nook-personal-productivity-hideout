from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QColorDialog, QSizeGrip, QApplication,
    QDialog, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import data as datastore

FONT = "Helvetica"


class TaskItem(QWidget):
    def __init__(self, task, accent, on_change, on_delete, edit_mode=False):
        super().__init__()
        self.task = task
        self.accent = accent
        self.on_change = on_change
        self.on_delete = on_delete
        self.edit_mode = edit_mode
        self.build()

    def build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        from PyQt6.QtWidgets import QCheckBox
        self.cb = QCheckBox()
        self.cb.setChecked(self.task["done"])
        self.cb.stateChanged.connect(self.toggle_done)
        layout.addWidget(self.cb)

        self.label = QLineEdit(self.task["text"])
        self.label.setReadOnly(True)
        self.label.mousePressEvent = lambda e: self.start_edit()
        self.label.returnPressed.connect(self.finish_edit)
        layout.addWidget(self.label)

        if self.edit_mode:
            del_btn = QPushButton("x")
            del_btn.setFixedSize(20, 20)
            del_btn.clicked.connect(self.on_delete)
            del_btn.setStyleSheet("""
                QPushButton { color: #666; background: transparent; border: none; font-size: 12px; font-weight: bold; }
                QPushButton:hover { color: #ff5555; }
            """)
            layout.addWidget(del_btn)

        self.apply_style()

    def apply_style(self):
        done = self.task["done"]
        text_color = "#505050" if done else "#cccccc"
        strike = "line-through" if done else "none"
        self.label.setStyleSheet(f"""
            QLineEdit {{
                color: {text_color};
                text-decoration: {strike};
                background: transparent;
                border: none;
                font-family: {FONT};
                font-size: 12px;
            }}
        """)
        self.cb.setStyleSheet(f"""
            QCheckBox {{ background: transparent; }}
            QCheckBox::indicator {{
                width: 13px; height: 13px;
                border: 1px solid {self.accent};
                border-radius: 3px;
                background: transparent;
            }}
            QCheckBox::indicator:checked {{ background: {self.accent}; }}
        """)

    def toggle_done(self):
        self.task["done"] = self.cb.isChecked()
        self.apply_style()
        self.on_change()

    def start_edit(self):
        self.label.setReadOnly(False)
        self.label.setFocus()

    def finish_edit(self):
        text = self.label.text().strip()
        if text:
            self.task["text"] = text
        self.label.setReadOnly(True)
        self.apply_style()
        self.on_change()


class CategoryWidget(QWidget):
    def __init__(self, cat, accent, on_change, on_delete_self, edit_mode=False, expanded=False, two_col=False):
        super().__init__()
        self.cat = cat
        self.accent = accent
        self.on_change = on_change
        self.on_delete_self = on_delete_self
        self.edit_mode = edit_mode
        self.expanded = expanded
        self.two_col = two_col
        self.setStyleSheet("background: transparent;")
        self.build()

    def build(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 4)
        self.main_layout.setSpacing(2)

        header_row = QHBoxLayout()
        done = sum(1 for t in self.cat["tasks"] if t["done"])
        total = len(self.cat["tasks"])

        self.header_btn = QPushButton(f"  {self.cat['name']}   {done}/{total}")
        self.header_btn.clicked.connect(self.toggle_expand)
        self._style_header()
        header_row.addWidget(self.header_btn)

        if self.edit_mode:
            del_btn = QPushButton("x")
            del_btn.setFixedSize(26, 26)
            del_btn.clicked.connect(self.on_delete_self)
            del_btn.setStyleSheet("""
                QPushButton { color: #666; background: transparent; border: none; font-size: 14px; font-weight: bold; }
                QPushButton:hover { color: #ff5555; }
            """)
            header_row.addWidget(del_btn)

        self.main_layout.addLayout(header_row)

        self.task_area = QVBoxLayout()
        self.task_area.setSpacing(1)
        self.main_layout.addLayout(self.task_area)

        if self.expanded:
            self.refresh_tasks()

    def _style_header(self):
        self.header_btn.setStyleSheet(f"""
            QPushButton {{
                background: #2a2a2a;
                color: {self.accent};
                border: 1px solid {self.accent};
                border-radius: 6px;
                padding: 7px 10px;
                text-align: left;
                font-family: {FONT};
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #303030; }}
        """)

    def toggle_expand(self):
        self.expanded = not self.expanded
        self.on_change(expand_toggle=True)

    def set_two_col(self, val):
        if val != self.two_col:
            self.two_col = val
            if self.expanded:
                self.refresh_tasks()

    def refresh_tasks(self):
        # clear task area without touching header
        while self.task_area.count():
            item = self.task_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        if not self.expanded:
            return

        tasks = self.cat["tasks"]

        if self.two_col and len(tasks) > 0:
            grid = QGridLayout()
            grid.setSpacing(2)
            for i, task in enumerate(tasks):
                idx = i
                w = TaskItem(
                    task, self.accent,
                    lambda: self.on_change(),
                    lambda checked=False, t=task: self.delete_task(t),
                    self.edit_mode
                )
                grid.addWidget(w, idx // 2, idx % 2)
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container.setLayout(grid)
            self.task_area.addWidget(container)
        else:
            for task in tasks:
                w = TaskItem(
                    task, self.accent,
                    lambda: self.on_change(),
                    lambda checked=False, t=task: self.delete_task(t),
                    self.edit_mode
                )
                self.task_area.addWidget(w)

        # add task input
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("new task")
        self.task_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: #888;
                border: none;
                border-bottom: 1px solid #2f2f2f;
                padding: 4px 2px;
                font-family: {FONT};
                font-size: 12px;
            }}
        """)
        self.task_input.returnPressed.connect(self.add_task)
        self.task_area.addWidget(self.task_input)

        clear_btn = QPushButton("clear completed")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: #444;
                background: transparent;
                border: none;
                font-size: 11px;
                font-family: {FONT};
                text-align: left;
                padding: 2px 0px;
            }}
            QPushButton:hover {{ color: {self.accent}; }}
        """)
        clear_btn.clicked.connect(self.clear_done)
        self.task_area.addWidget(clear_btn)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_task(self):
        text = self.task_input.text().strip()
        if not text:
            return
        self.cat["tasks"].append({"text": text, "done": False})
        self.task_input.clear()
        self.on_change()
        self.refresh_tasks()

    def delete_task(self, task):
        if task in self.cat["tasks"]:
            self.cat["tasks"].remove(task)
        self.on_change()
        self.refresh_tasks()

    def clear_done(self):
        self.cat["tasks"] = [t for t in self.cat["tasks"] if not t["done"]]
        self.on_change()
        self.refresh_tasks()


class SettingsDialog(QDialog):
    def __init__(self, parent, accent, bg, on_accent, on_bg):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.accent = accent
        self.bg = bg
        self.on_accent = on_accent
        self.on_bg = on_bg
        self.setStyleSheet("""
            QDialog {
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
            }
            QLabel {
                color: #666;
                font-size: 10px;
                font-family: Helvetica;
            }
        """)
        self.build()

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # accent
        layout.addWidget(QLabel("ACCENT COLOR"))
        accent_btn = QPushButton()
        accent_btn.setFixedHeight(28)
        accent_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.accent};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{ opacity: 0.8; }}
        """)
        accent_btn.clicked.connect(self.pick_accent)
        layout.addWidget(accent_btn)

        # bg
        layout.addWidget(QLabel("BACKGROUND COLOR"))
        bg_btn = QPushButton()
        bg_btn.setFixedHeight(28)
        bg_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.bg};
                border: 1px solid #333;
                border-radius: 4px;
            }}
        """)
        bg_btn.clicked.connect(self.pick_bg)
        layout.addWidget(bg_btn)

        self.adjustSize()

    def pick_accent(self):
        color = QColorDialog.getColor(QColor(self.accent), self, "Accent color")
        if color.isValid():
            self.accent = color.name()
            self.on_accent(self.accent)
            self.close()

    def pick_bg(self):
        color = QColorDialog.getColor(QColor(self.bg), self, "Background color")
        if color.isValid():
            self.bg = color.name()
            self.on_bg(self.bg)
            self.close()


class NookWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.data = datastore.load()
        self.accent = self.data.get("accent", "#4EC9B0")
        self.bg = self.data.get("bg", "#1e1e1e")
        self.edit_mode = False
        self._drag_pos = None
        self._at_max_height = False
        self.cat_widgets = []
        self.initUI()

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # --- WINDOW SIZE: edit these ---
        self.setMinimumWidth(260)
        self.setMaximumWidth(300)
        self.setMinimumHeight(400)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setMaximumHeight(screen.height() - 40)
        self.resize(300, 400)
        # --------------------------------

        self.root = QWidget(self)
        self.root.setObjectName("nook_root")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.root)

        self.main_layout = QVBoxLayout(self.root)
        self.main_layout.setContentsMargins(12, 12, 12, 8)
        self.main_layout.setSpacing(6)

        self.apply_bg()
        self.build_ui()

    def apply_bg(self):
        self.root.setStyleSheet(f"""
            QWidget#nook_root {{
                background: {self.bg};
                border-radius: 10px;
                border: 1px solid #2a2a2a;
            }}
        """)

    def build_ui(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # top bar
        top_bar = QHBoxLayout()

        # --- CATEGORY INPUT PLACEHOLDER: edit the string below ---
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("add categrory")
        # ----------------------------------------------------------
        self.cat_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: #999;
                border: none;
                border-bottom: 1px solid #2a2a2a;
                padding: 4px 2px;
                font-family: {FONT};
                font-size: 12px;
            }}
        """)
        self.cat_input.returnPressed.connect(self.add_category)
        top_bar.addWidget(self.cat_input)

        edit_btn = QPushButton("✎")
        edit_btn.setFixedSize(26, 26)
        edit_btn.setCheckable(True)
        edit_btn.setChecked(self.edit_mode)
        edit_btn.clicked.connect(self.toggle_edit_mode)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                color: {'#ff6b6b' if self.edit_mode else '#555'};
                background: transparent;
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{ color: {self.accent}; }}
            QPushButton:checked {{ color: #ff6b6b; }}
        """)
        top_bar.addWidget(edit_btn)

        settings_btn = QPushButton("\u2699")
        settings_btn.setFixedSize(26, 26)
        settings_btn.clicked.connect(self.open_settings)
        settings_btn.setStyleSheet(f"""
            QPushButton {{
                color: #555;
                background: transparent;
                border: none;
                font-size: 15px;
            }}
            QPushButton:hover {{ color: {self.accent}; }}
        """)
        top_bar.addWidget(settings_btn)
        self.main_layout.addLayout(top_bar)

        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #2a2a2a;")
        self.main_layout.addWidget(line)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.cat_container = QWidget()
        self.cat_container.setStyleSheet("background: transparent;")
        self.cat_layout = QVBoxLayout(self.cat_container)
        self.cat_layout.setSpacing(5)
        self.cat_layout.setContentsMargins(0, 0, 0, 0)
        self.cat_layout.addStretch()

        self.scroll.setWidget(self.cat_container)
        self.main_layout.addWidget(self.scroll)

        grip = QSizeGrip(self)
        grip.setStyleSheet("background: transparent;")
        self.main_layout.addWidget(
            grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight
        )

        self.render_categories()

    def render_categories(self):
        self.cat_widgets = []
        while self.cat_layout.count() > 1:
            item = self.cat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        expanded_names = set(self.data.get("expanded", []))
        at_max = self._at_max_height

        for cat in self.data["categories"]:
            is_expanded = cat["name"] in expanded_names
            w = CategoryWidget(
                cat=cat,
                accent=self.accent,
                on_change=self.on_category_change,
                on_delete_self=self._make_delete_fn(cat),
                edit_mode=self.edit_mode,
                expanded=is_expanded,
                two_col=at_max
            )
            self.cat_layout.insertWidget(self.cat_layout.count() - 1, w)
            self.cat_widgets.append(w)

    def _make_delete_fn(self, cat):
        # capture cat correctly — avoids the lambda-in-loop bug
        def delete():
            if cat in self.data["categories"]:
                self.data["categories"].remove(cat)
            self.save_and_render()
        return delete

    def on_category_change(self, expand_toggle=False):
        if expand_toggle:
            # sync expanded state from widgets into data before saving
            expanded = []
            for w in self.cat_widgets:
                if w.expanded:
                    expanded.append(w.cat["name"])
            self.data["expanded"] = expanded
            datastore.save(self.data)
            # refresh only the tasks inside each widget, don't rebuild everything
            for w in self.cat_widgets:
                w.refresh_tasks()
        else:
            datastore.save(self.data)

    def save_and_render(self):
        datastore.save(self.data)
        self.render_categories()

    def add_category(self):
        name = self.cat_input.text().strip()
        if not name:
            return
        self.data["categories"].append({"name": name, "tasks": []})
        self.cat_input.clear()
        self.save_and_render()

    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        self.build_ui()

    def open_settings(self):
        dlg = SettingsDialog(
            self,
            self.accent,
            self.bg,
            on_accent=self.set_accent,
            on_bg=self.set_bg
        )
        # position near gear button
        pos = self.mapToGlobal(self.rect().bottomRight())
        dlg.move(pos.x() - dlg.sizeHint().width() - 10, pos.y() - 120)
        dlg.exec()

    def set_accent(self, color):
        self.accent = color
        self.data["accent"] = color
        datastore.save(self.data)
        self.build_ui()

    def set_bg(self, color):
        self.bg = color
        self.data["bg"] = color
        datastore.save(self.data)
        self.apply_bg()
        self.build_ui()

    def check_two_col(self):
        at_max = self.height() >= self.maximumHeight()
        if at_max != self._at_max_height:
            self._at_max_height = at_max
            for w in self.cat_widgets:
                w.set_two_col(at_max)

    def position_top_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.top() + 20)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.check_two_col()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def focusOutEvent(self, e):
        self.hide()