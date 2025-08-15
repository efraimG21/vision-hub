

import ipaddress
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGroupBox, QFormLayout, QLineEdit, QMessageBox
)
from app import APP_NAME
from app.services.logger import get_logger


class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.logger = get_logger('SettingsWidget')
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Settings – IP Configuration")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px; color: white;")
        layout.addWidget(title)

        form_group = QGroupBox()
        form_layout = QFormLayout()

        form_group.setStyleSheet("""
                        QGroupBox {
                            border: 2px solid gray;
                            border-radius: 15px;
                        }
                """)

        self.ip_fields = []
        self.name_fields = []

        settings = QSettings(APP_NAME, "AxisApp")

        for i in range(4):
            ip_input = QLineEdit()
            ip_input.setPlaceholderText("e.g., 127.0.0.1")
            ip_input.setInputMask("000.000.000.000;_")
            ip_input.setFixedWidth(180)
            ip_input.setText(settings.value(f"device_{i}/ip"))

            name_input = QLineEdit()
            name_input.setPlaceholderText("Nickname")
            name_input.setFixedWidth(150)
            name_input.setText(settings.value(f"device_{i}/name"))

            ip_input.setStyleSheet(self.input_style())
            name_input.setStyleSheet(self.input_style())

            self.ip_fields.append(ip_input)
            self.name_fields.append(name_input)

            row_layout = QHBoxLayout()
            row_layout.setSpacing(20)
            row_layout.addWidget(ip_input)
            row_layout.addWidget(name_input)

            row_widget = QWidget()
            row_widget.setLayout(row_layout)

            label = QLabel(f"Device {i+1}:")
            label.setStyleSheet("font-size: 16px; color: white;")
            form_layout.addRow(label, row_widget)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        save_btn = QPushButton("Save Configuration")
        save_btn.setFixedHeight(40)
        save_btn.setStyleSheet(self.btn_style())
        save_btn.clicked.connect(self.save_configuration)

        clear_btn = QPushButton("Clear Configuration")
        clear_btn.setFixedHeight(40)
        clear_btn.setStyleSheet(self.btn_style())
        clear_btn.clicked.connect(self.clear_configuration)

        close_app_btn = QPushButton("Close app")
        close_app_btn.setFixedHeight(40)
        close_app_btn.setStyleSheet(self.btn_style())

        layout.addWidget(save_btn)
        layout.addWidget(clear_btn)
        layout.addWidget(close_app_btn)
        layout.addStretch()
        self.setLayout(layout)

    def btn_style(self):
        return """
            QPushButton {
                font-size: 16px;
                background-color: #0078d4;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
        """
    def input_style(self):
        return """
            QLineEdit {
                padding: 6px;
                font-size: 14px;
                border: 1px solid #aaa;
                border-radius: 4px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
                color: white
            }
        """

    def is_valid_ip(self, ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def save_configuration(self):
        settings = QSettings(APP_NAME, "AxisApp")

        for i, (ip_field, name_field) in enumerate(zip(self.ip_fields, self.name_fields)):
            ip = ip_field.text().strip()
            name = name_field.text().strip()

            if ip and not self.is_valid_ip(ip):
                ip_field.clear()
                settings.setValue(f"device_{i}/ip", '')
                continue

            settings.setValue(f"device_{i}/ip", ip)
            settings.setValue(f"device_{i}/name", name)

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Saved")
        msg.setText("Configuration saved successfully!")
        msg.setStyleSheet("""
            QMessageBox {
                color: white;
                font-size: 16px;
            }
            QLabel{
                color: white;
            }
            QPushButton {
                background-color: #444;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        msg.exec()

    def clear_configuration(self):
        msg_box = QMessageBox(
            QMessageBox.Question,
            "Clear Settings",
            "Are you sure you want to clear all saved configurations?",
            QMessageBox.Yes | QMessageBox.No,
            self
        )
        msg_box.setStyleSheet("""
            QMessageBox {
                color: white;
                font-size: 16px;
            }
            QLabel{
                color: white;
            }
            QPushButton {
                background-color: #444;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            settings = QSettings(APP_NAME, "AxisApp")
            settings.clear()

            for ip_field, name_field in zip(self.ip_fields, self.name_fields):
                ip_field.clear()
                name_field.clear()

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Clearing")
            msg.setText("Configuration clearing successfully!")
            msg.setStyleSheet("""
                QMessageBox {
                    color: white;
                    font-size: 16px;
                }
                QLabel{
                    color: white;
                }
                QPushButton {
                    background-color: #444;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)
            msg.exec()
