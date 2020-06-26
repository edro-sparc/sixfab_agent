import os
import logging
import logging.handlers


def initialize_logger():
    logging_file_path = os.path.expanduser("~")+"/.sixfab/"
    
    if not os.path.exists(logging_file_path):
        os.mkdir(logging_file_path)

    logger = logging.getLogger("agent")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
    log_file_handler = logging.handlers.TimedRotatingFileHandler(filename=logging_file_path+"agent-log", when="midnight", backupCount=3)
    log_file_handler.setFormatter(formatter)

    logger.addHandler(log_file_handler)

    return logger