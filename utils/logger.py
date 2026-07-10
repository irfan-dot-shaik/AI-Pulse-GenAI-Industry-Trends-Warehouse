# =============================================================================
# utils/logger.py — AI Pulse Project
# =============================================================================
#
# PURPOSE:
#   Sets up a centralized logger that:
#     1. Prints log messages to the console (with color-friendly formatting)
#     2. Saves log messages to a file in the logs/ directory
#
# CONCEPT — Why Use logging Instead of print()?
#
#   print("Data fetched")          ← No timestamp, no level, no file output
#   logger.info("Data fetched")    ← Timestamp + level + saved to file
#
#   Real pipelines run unattended (no one watching the terminal).
#   Log files are how you debug what happened hours or days ago.
#
# CONCEPT — Log Levels (from least to most severe):
#   DEBUG    → Very detailed info, used during development
#   INFO     → Normal operation messages ("Pipeline started", "10 records inserted")
#   WARNING  → Something unusual but not an error ("API returned 0 results")
#   ERROR    → Something failed ("Database connection refused")
#   CRITICAL → The system cannot continue ("Config missing, aborting")
#
# CONCEPT — Handlers:
#   A handler decides WHERE log messages go.
#   We use TWO handlers:
#     - StreamHandler → sends logs to the console
#     - FileHandler   → saves logs to a file
#   Both handlers receive the same messages, sent to different destinations.
#
# =============================================================================

import logging                   # Built-in Python logging module
import sys                       # Built-in: access to stdout (console output)

# Import our centralized config so log level and file path come from settings
from config.settings import LOG_LEVEL, LOG_FILE_PATH


def get_logger(name: str) -> logging.Logger:
    """
    Create and return a configured logger for a given module.

    USAGE in other files:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Pipeline started")
        logger.error("Something failed")

    Args:
        name (str): The name of the module requesting the logger.
                    We pass __name__ from the calling module, which gives
                    us the module's full dotted name (e.g., "ingestion.gnews_client").
                    This makes it easy to see which module generated each log line.

    Returns:
        logging.Logger: A fully configured logger instance.

    WHY __name__?
        Each module gets its own logger named after itself.
        In the log output you'll see:
            [ingestion.gnews_client] Fetching articles from GNews API...
            [database.warehouse]     Inserting 10 records into raw_ai_news...
        This tells you exactly which part of the pipeline produced each message.
    """

    # ---------------------------------------------------------------------------
    # Step 1: Get or create the logger
    # ---------------------------------------------------------------------------
    # logging.getLogger(name) is idempotent:
    # If a logger with this name already exists, it returns the same one.
    # This means calling get_logger("ingestion.gnews_client") 10 times
    # always returns the same logger object — no duplicates.
    logger = logging.getLogger(name)

    # ---------------------------------------------------------------------------
    # Step 2: Set the minimum log level
    # ---------------------------------------------------------------------------
    # getattr(logging, "INFO") is equivalent to logging.INFO
    # We use getattr because LOG_LEVEL is a string from the .env file,
    # and we need to convert it to the actual logging constant (an integer).
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # ---------------------------------------------------------------------------
    # Step 3: Avoid adding duplicate handlers
    # ---------------------------------------------------------------------------
    # If logger.handlers is already populated, the logger was already configured.
    # Without this check, every call to get_logger() would add MORE handlers,
    # causing each message to be printed/saved multiple times.
    if logger.handlers:
        return logger

    # ---------------------------------------------------------------------------
    # Step 4: Define the log message FORMAT
    # ---------------------------------------------------------------------------
    # This controls what each log line looks like.
    #
    # %(asctime)s    → Timestamp: "2026-06-24 18:30:01,234"
    # %(name)s       → Logger name: "ingestion.gnews_client"
    # %(levelname)s  → Level: "INFO", "ERROR", etc.
    # %(message)s    → The actual message you logged
    #
    # Example output:
    # 2026-06-24 18:30:01,234 | ingestion.gnews_client | INFO | Fetching 10 articles...
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ---------------------------------------------------------------------------
    # Step 5: Console Handler (StreamHandler)
    # ---------------------------------------------------------------------------
    # Sends log messages to sys.stdout (your terminal/console).
    # This is what you see when you run: python main.py
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ---------------------------------------------------------------------------
    # Step 6: File Handler (FileHandler)
    # ---------------------------------------------------------------------------
    # Saves log messages to a file on disk.
    # This is what you read AFTER a pipeline run to understand what happened.
    #
    # We first create the parent directory (logs/) if it doesn't exist.
    # exist_ok=True means: don't raise an error if the folder already exists.
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # "a" mode = append. New runs add to the same file.
    # Use "w" mode if you want a fresh log file every run.
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # ---------------------------------------------------------------------------
    # Step 7: Prevent log propagation
    # ---------------------------------------------------------------------------
    # Python's logging system has a hierarchy: child loggers pass messages to
    # the root logger, which might also print them. Setting propagate=False
    # prevents double-printing when the root logger is configured separately.
    logger.propagate = False

    return logger
