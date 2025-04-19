import logging
from logging.handlers import TimedRotatingFileHandler
import os
import platform

def setup_logging():
    # Configuring the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Setting the logging level to INFO

    # Get the directory of the current script
    log_directory = 'log'

    # Ensure the log directory exists (create it if it doesn't)
    os.makedirs(log_directory, exist_ok=True)

    # Define the log file path
    log_file_path = os.path.join(log_directory, 'automated-backup.log')

    # Configure the TimedRotatingFileHandler to rotate logs weekly
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when='W0',         # Rotate every Monday ('W0' indicates Monday as the start of the week)
        interval=1,        # Rotate every week
        backupCount=4      # Keep the logs of the last 4 weeks
    )
    # Define the log message format for file handler
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    # Configure the console handler to also log messages to the console
    console_handler = logging.StreamHandler()
    # Define the log message format for console handler
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # Add the console handler to the logger
    logger.addHandler(console_handler)
