

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QWidget, QGridLayout, QSizePolicy, QApplication

from app import APP_NAME

from app.services.logger import get_logger
from app.widgets.panel_widget import PanelWidget

class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = get_logger('HomeWidget')

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)

        self.settings = QSettings(APP_NAME, "AxisApp")

        self.panels = []

        for row in range(2):
            for col in range(2):
                panel_index = row * 2 + col + 1

                stream_nickname = self.settings.value(f"device_{panel_index - 1}/name")
                stream_ip = self.settings.value(f"device_{panel_index - 1}/ip")

                panel_title = stream_nickname if stream_nickname else f'Panel {panel_index}'

                panel = PanelWidget(panel_title, stream_ip=stream_ip, panel_index=panel_index -1)

                panel.doubleClicked.connect(self.toggle_panel_view)
                self.grid_layout.addWidget(panel, row, col)
                self.panels.append(panel)

        self.single_panel_mode = False
        self.single_panel_widget = None
        self.setLayout(self.grid_layout)
        self.logger.debug(f'video label size: {self.panels[0].video_label.size()}')

    def toggle_panel_view(self, panel_title):
        if not self.single_panel_mode:
            # Save current layout state
            for panel in self.panels:
                panel._original_size_policy = panel.sizePolicy()
                panel._original_min_size = panel.minimumSize()

            # Find and isolate the clicked panel
            for panel in self.panels:
                if panel.title == panel_title:
                    self.single_panel_widget = panel
                    break

            for panel in self.panels:
                panel.setVisible(False)

            self.grid_layout.addWidget(self.single_panel_widget, 0, 0, 2, 2)
            self.single_panel_widget.setVisible(True)
            self.single_panel_mode = True

        else:
            for i, panel in enumerate(self.panels):
                row = i // 2
                col = i % 2
                self.grid_layout.addWidget(panel, row, col)
                panel.setVisible(True)

                # Restore original size policy and size
                if hasattr(panel, '_original_min_size'):
                    panel.setMinimumSize(panel._original_min_size)
                if hasattr(panel, '_original_size_policy'):
                    panel.setSizePolicy(panel._original_size_policy)

                panel.updateGeometry()

            self.single_panel_mode = False
            self.single_panel_widget = None
            self.grid_layout.invalidate()
            self.updateGeometry()
