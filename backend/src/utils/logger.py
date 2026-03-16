"""
Logging Configuration
Location: backend/src/utils/logger.py
"""

import logging
import sys
from pathlib import Path
from loguru import logger
from ..config.settings import config

# Remove default handler
logger.remove()

# Add console handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
    level=config.LOG_LEVEL.upper(),
    colorize=True
)

# Add file handler
log_path = Path(config.LOG_DIR) / "app.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

logger.add(
    str(log_path),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
    level="INFO",
    rotation="10 MB",
    retention="30 days",
    compression="zip"
)

def setup_logging():
    """Setup logging configuration"""
    logger.info(f"Logging configured. Level: {config.LOG_LEVEL}")
    return logger

def get_logger(name: str):
    """Get logger instance"""
    return logger.bind(name=name)