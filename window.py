import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QSizeGrip, QApplication,
    QDialog, QLabel, QToolTip
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
import data as datastore

FONT = "Helvetica"

# ── Colour presets — edit these yourself ────────────────────────────
BG_PRESETS = [
    ("#0a0a0a", "Black"),
    ("#8d99ae", "Light Grey"),
    ("#0d1b2a", "Navy"),
    ("#003049", "Navy02"),
    ("#f7cad0", "Light Pink"),
    ("#8364e8", "Purple"),
    ("#a3b18a", "Sage Green"),
    ("#3a5a40", "Dark Green"),
    ("#caf0f8", "Light Blue"),
    ("#1f0021", "Deep Wine"),
    ("#f0f0f0", "White"),
]

ACCENT_PRESETS = [
    ("#34073d", "Deep purple"),
    ("#0e1c26", "Black"),
    ("#b7e4c7", "Light Green"),
    ("#d9dace", "Pale White"),
    ("#ffffff", "White"),
    ("#ff6b6b", "Red"),
    ("#e7bc91", "Light Brown"),
    ("#f0c040", "Gold"),
    ("#7ec8e3", "Sky"),
    ("#a78bfa", "Violet"),
]
# ────────────────────────────────────────────────────────────────────


# ── Custom painted gear button (no emoji) ───────────────────────────
class GearButton(QPushButton):
    def __init__(self, accent="#555"):
        super().__init__()
        self.setFixedSize(26, 26)
        self._base  = "#555"
        self._hover = accent
        self._hovering = False
        self.setStyleSheet("background: transparent; border: none;")

    def set_accent(self, accent):
        self._hover = accent
        self.update()

    def enterEvent(self, e):
        self._hovering = True
        self.update()

    def leaveEvent(self, e):
        self._hovering = False
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self._hover if self._hovering else self._base)
        p.setPen(QPen(color, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy   = 13.0, 13.0
        n_teeth  = 6
        r_outer  = 5.8
        r_inner  = 4.2
        r_hole   = 2.1

        pts = []
        for i in range(n_teeth * 2):
            angle = math.pi * 2 * i / (n_teeth * 2)
            r = r_outer if i % 2 == 0 else r_inner
            pts.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))

        p.drawPolygon(QPolygonF(pts))
        p.drawEllipse(QPointF(cx, cy), r_hole, r_hole)
        p.end()


# ── Task item ────────────────────────────────────────────────────────
class TaskItem(QWidget):
    def __init__(self, task, accent, on_change, on_delete, edit_mode=False):
        super().__init__()
        self.task      = task
        self.accent    = accent
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
                QPushButton { color: #555; background: transparent; border: none; font-size: 12px; }
                QPushButton:hover { color: #ff5555; }
            """)
            layout.addWidget(del_btn)

        self.apply_style()

    def apply_style(self):
        done       = self.task["done"]
        text_color = "#505050" if done else "#cccccc"
        strike     = "line-through" if done else "none"
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


# ── Category widget ──────────────────────────────────────────────────
class CategoryWidget(QWidget):
    def __init__(self, cat, accent, on_change, on_delete_self,
                 edit_mode=False, expanded=False, two_col=False):
        super().__init__()
        self.cat           = cat
        self.accent        = accent
        self.on_change     = on_change
        self.on_delete_self = on_delete_self
        self.edit_mode     = edit_mode
        self.expanded      = expanded
        self.two_col       = two_col
        self.setStyleSheet("background: transparent;")
        self.build()

    def build(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 4)
        self.main_layout.setSpacing(2)

        header_row = QHBoxLayout()
        done  = sum(1 for t in self.cat["tasks"] if t["done"])
        total = len(self.cat["tasks"])

        self.header_btn = QPushButton(f"  {self.cat['name']}   {done}/{total}")
        self.header_btn.clicked.connect(self.toggle_expand)
        self._style_header()
        header_row.addWidget(self.header_btn)

        if self.edit_mode:
            del_btn = QPushButton("x")
            del_btn.setFixedSize(24, 24)
            del_btn.clicked.connect(self.on_delete_self)
            del_btn.setStyleSheet("""
                QPushButton { color: #555; background: transparent; border: none; font-size: 13px; }
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
        # thin left-accent border, no bold
        self.header_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {self.accent};
                border: 1px solid #2a2a2a;
                border-left: 2px solid {self.accent};
                border-radius: 4px;
                padding: 5px 8px;
                text-align: left;
                font-family: {FONT};
                font-size: 13px;
                font-weight: normal;
            }}
            QPushButton:hover {{ background: #1a1a1a; }}
        """)

    def update_count(self):
        done  = sum(1 for t in self.cat["tasks"] if t["done"])
        total = len(self.cat["tasks"])
        self.header_btn.setText(f"  {self.cat['name']}   {done}/{total}")

    def toggle_expand(self):
        self.expanded = not self.expanded
        self.on_change(expand_toggle=True)

    def set_two_col(self, val):
        if val != self.two_col:
            self.two_col = val
            if self.expanded:
                self.refresh_tasks()

    def refresh_tasks(self):
        while self.task_area.count():
            item = self.task_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        self.update_count()

        if not self.expanded:
            return

        tasks = self.cat["tasks"]

        if self.two_col and len(tasks) > 0:
            grid = QGridLayout()
            grid.setSpacing(2)
            for i, task in enumerate(tasks):
                w = TaskItem(
                    task, self.accent,
                    lambda: self.on_change(),
                    lambda checked=False, t=task: self.delete_task(t),
                    self.edit_mode
                )
                grid.addWidget(w, i // 2, i % 2)
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

        # task input — color set so typed text is visible, placeholder stays dim
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("new task")
        self.task_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: #cccccc;
                border: none;
                border-bottom: 1px solid #2f2f2f;
                padding: 4px 2px;
                font-family: {FONT};
                font-size: 12px;
            }}
        """)
        _p = self.task_input.palette()
        _p.setColor(_p.ColorRole.PlaceholderText, QColor("#444444"))
        self.task_input.setPalette(_p)


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


# ── Settings dialog — preset swatch grids ───────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, parent, accent, bg, on_accent, on_bg):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.accent    = accent
        self.bg        = bg
        self.on_accent = on_accent
        self.on_bg     = on_bg
        self.setStyleSheet("""
            QDialog {
                background: #1a1a1a;
                border: 1px solid #2e2e2e;
                border-radius: 8px;
            }
            QLabel {
                color: #555;
                font-size: 9px;
                font-family: Helvetica;
                letter-spacing: 1px;
            }
        """)
        self.build()

    def _swatch_row(self, label_text, presets, current, on_pick):
        """Labelled row of clickable colour swatches."""
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        vl = QVBoxLayout(wrapper)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(5)
        vl.addWidget(QLabel(label_text))

        row = QHBoxLayout()
        row.setSpacing(5)
        row.setContentsMargins(0, 0, 0, 0)

        for hex_val, name in presets:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setToolTip(name)
            is_active = hex_val.lower() == current.lower()
            border = f"2px solid #ffffff" if is_active else "1px solid #333"
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_val};
                    border: {border};
                    border-radius: 3px;
                }}
                QPushButton:hover {{ border: 2px solid #888; }}
            """)
            btn.clicked.connect(lambda checked=False, h=hex_val, fn=on_pick: (fn(h), self.close()))
            row.addWidget(btn)

        row.addStretch()
        vl.addLayout(row)
        return wrapper

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        layout.addWidget(self._swatch_row("ACCENT", ACCENT_PRESETS, self.accent, self.on_accent))
        layout.addWidget(self._swatch_row("BACKGROUND", BG_PRESETS, self.bg, self.on_bg))

        self.adjustSize()


# ── Main window ──────────────────────────────────────────────────────
class NookWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.data        = datastore.load()
        self.accent      = self.data.get("accent", "#4EC9B0")
        self.bg          = self.data.get("bg", "#1e1e1e")
        self.edit_mode   = False
        self._drag_pos   = None
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

        self.setMinimumWidth(260)
        self.setMaximumWidth(300)
        self.setMinimumHeight(400)
        screen = QApplication.primaryScreen().availableGeometry()
        self.setMaximumHeight(screen.height() - 40)
        self.resize(260, 400)

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

        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("add category")
        self.cat_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: #cccccc;
                border: none;
                border-bottom: 1px solid #2a2a2a;
                padding: 4px 2px;
                font-family: {FONT};
                font-size: 12px;
            }}
        """)
        _p = self.cat_input.palette()
        _p.setColor(_p.ColorRole.PlaceholderText, QColor("#444444"))
        self.cat_input.setPalette(_p)   

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

        # clean painted gear — not an emoji
        self.gear_btn = GearButton(accent=self.accent)
        self.gear_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.gear_btn)

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
        def delete():
            if cat in self.data["categories"]:
                self.data["categories"].remove(cat)
            self.save_and_render()
        return delete

    def on_category_change(self, expand_toggle=False):
        if expand_toggle:
            expanded = []
            for w in self.cat_widgets:
                if w.expanded:
                    expanded.append(w.cat["name"])
            self.data["expanded"] = expanded
            datastore.save(self.data)
            for w in self.cat_widgets:
                w.update_count()
            for w in self.cat_widgets:
                w.refresh_tasks()
        else:
            datastore.save(self.data)
            for w in self.cat_widgets:
                w.update_count()

    def save_and_render(self):
        datastore.save(self.data)
        if hasattr(self, 'cat_input'):
            self.cat_input.clear()
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
        pos = self.mapToGlobal(self.rect().bottomRight())
        dlg.move(pos.x() - dlg.sizeHint().width() - 10, pos.y() - 130)
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