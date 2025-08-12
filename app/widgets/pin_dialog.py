
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy, QDialog

class PinDialog(QDialog):
    def __init__(self, parent=None, pin_length=4, correct_pin="1234"):
        super().__init__(parent)

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setFixedSize(300, 425)
        self.pin_length = pin_length
        self.correct_pin = correct_pin
        self.entered_pin = ""
        self.setStyleSheet("""
                        QDialog {
                            border-radius: 25px;
                        }
                        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        self.display = QLabel("•" * 0 + "_" * self.pin_length)
        self.display.setAlignment(Qt.AlignCenter)
        self.display.setStyleSheet("font-size: 28px; color: white;")
        layout.addWidget(self.display)

        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("color: red; font-size: 16px;")
        layout.addWidget(self.error_label)

        buttons = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["Clear", "0", "⌫"]
        ]

        for row in buttons:
            row_layout = QHBoxLayout()
            for label in row:
                btn = QPushButton(label)
                btn.setFixedSize(80, 60)
                btn.setStyleSheet("""
                    QPushButton {
                        font-size: 20px;
                        background-color: #333;
                        color: white;
                        border-radius: 5px;
                    }
                    QPushButton:pressed {
                        background-color: #555;
                    }
                """)
                btn.clicked.connect(self.handle_button)
                row_layout.addWidget(btn)
            layout.addLayout(row_layout)

        footer = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")

        for b in (ok_btn, cancel_btn):
            b.setFixedHeight(40)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setStyleSheet("""
                QPushButton {
                    font-size: 18px;
                    background-color: #0078d4;
                    color: white;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #005fa3;
                }
            """)

        ok_btn.clicked.connect(self.validate_pin)
        cancel_btn.clicked.connect(self.reject)

        footer.addWidget(ok_btn)
        footer.addWidget(cancel_btn)
        layout.addLayout(footer)

    def handle_button(self):
        text = self.sender().text()
        if text == "Clear":
            self.entered_pin = ""
        elif text == "⌫":
            self.entered_pin = self.entered_pin[:-1]
        elif text.isdigit() and len(self.entered_pin) < self.pin_length:
            self.entered_pin += text
        self.update_display()

    def update_display(self):
        masked = "•" * len(self.entered_pin)
        remaining = "_" * (self.pin_length - len(self.entered_pin))
        self.display.setText(masked + remaining)
        self.error_label.setText("")

    def validate_pin(self):
        if self.entered_pin == self.correct_pin:
            self.accept()
        else:
            self.error_label.setText("Wrong code!")
            self.entered_pin = ""
            self.update_display()
