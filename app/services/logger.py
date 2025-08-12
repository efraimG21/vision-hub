import logging

class ColoredFormatter(logging.Formatter):
    """Custom formatter to color the entire log line based on the log level."""
    COLORS = {
        'DEBUG': '\033[34m',   # Blue
        'INFO': '\033[32m',    # Green
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',   # Red
        'CRITICAL': '\033[35m' # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Format the message as usual.
        formatted_message = super().format(record)
        # Get the color for the current log level.
        color = self.COLORS.get(record.levelname, '')
        # Wrap the entire message in the color code.
        return f"{color}{formatted_message}{self.RESET}"

class OnlyInfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO

def get_logger(name: str) -> logging.Logger:
    """Creates and returns a logger with colored output for the entire line."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create a stream handler for console output.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Define the log message format.
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = ColoredFormatter(log_format)
    console_handler.setFormatter(formatter)

    # Prevent adding multiple handlers in interactive environments.
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


def add_csv_handler(logger: logging.Logger, filename: str) -> None:
    """
    Adds a FileHandler that writes only INFO level log entries to a CSV file.
    """
    csv_handler = logging.FileHandler(filename)
    # Set to the lowest level so all messages pass the level check,
    # but our filter will only allow INFO records.
    csv_handler.setLevel(logging.INFO)

    # Add the custom filter to allow only INFO level messages.
    csv_handler.addFilter(OnlyInfoFilter())

    # Define the CSV format: Each field is wrapped in quotes.
    csv_format = '"%(asctime)s","%(name)s","%(levelname)s","%(message)s"'
    csv_formatter = logging.Formatter(csv_format)
    csv_handler.setFormatter(csv_formatter)

    logger.addHandler(csv_handler)
