
from PySide6.QtCore import QObject, Signal, QRunnable


class _RefreshSignals(QObject):
    refresh_panel = Signal(object)   # emits a PanelWidget
    finished = Signal()

class _RefreshTask(QRunnable):
    def __init__(self, panels):
        super().__init__()
        self.signals = _RefreshSignals()
        self._panels = panels

    def run(self):
        # Emit a signal for each panel; UI work happens in the main thread.
        for p in self._panels:
            self.signals.refresh_panel.emit(p)
        self.signals.finished.emit()