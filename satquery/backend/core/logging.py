import logging
import sys

def setup_logging(level=logging.INFO):
    logger = logging.getLogger("satquery")
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if setup_logging is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logging()
