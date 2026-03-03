import logging
from PySide6.QtCore import QObject, Signal

class QtLogHandler(logging.Handler, QObject):
    """
    Custom logging handler that emits a Qt signal for each log record.
    This allows logs to be displayed in a QTextEdit or other UI widget.
    """
    log_signal = Signal(str, str)  # level, message

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        ))

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(record.levelname, msg)
