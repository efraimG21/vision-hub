
import psutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

class BatteryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.percentage_label = QLabel("0%")
        self.percentage_label.setStyleSheet("font-size: 12px; color: white;")
        self.percentage_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        self.percentage_label.setFixedHeight(14)

        self.svg_widget = QSvgWidget()
        self.svg_widget.setFixedSize(40, 20)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.percentage_label)
        layout.addWidget(self.svg_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_battery)
        self.timer.start(5000)
        self.update_battery()

    def update_battery(self):
        battery = psutil.sensors_battery()
        if battery is None:
            self.percentage_label.setText("N/A")
            self.svg_widget.hide()
            return

        level = battery.percent
        charging = battery.power_plugged
        self.percentage_label.setText(f"{level}%")
        self.svg_widget.show()

        color = "green" if level >= 50 else "orange" if level >= 20 else "red"
        level_width = int(52 * (level / 100))
        svg_data = f"""
            <svg width='64' height='32' viewBox='0 0 64 32' xmlns='http://www.w3.org/2000/svg'>
              <rect x='2' y='6' width='56' height='20' rx='3' ry='3' stroke='black' stroke-width='2' fill='none'/>
              <rect x='4' y='8' width='{level_width}' height='16' rx='2' ry='2' fill='{color}'/>
              <rect x='58' y='12' width='4' height='8' rx='1' ry='1' fill='black'/>
              {"<text x='20' y='20' font-size='12' fill='white'>\u26a1</text>" if charging else ""}
            </svg>
        """
        self.svg_widget.load(svg_data.encode("utf-8"))
