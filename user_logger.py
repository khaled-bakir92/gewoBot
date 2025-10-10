#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User-Specific Logger - Multi-User Logging Support
==================================================

Creates separate log files for each user's operations.

Author: Gewobag Bot Team
Version: 2.1
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class UserLogger:
    """Manages user-specific logging."""

    def __init__(self, username: str, log_dir: Path, log_type: str = "main"):
        """
        Initialize user-specific logger.

        Args:
            username: Username for the logger
            log_dir: Directory to store log files (usually users/{username}/logs/)
            log_type: Type of log ('main', 'scraping', 'applications')
        """
        self.username = username
        self.log_dir = log_dir
        self.log_type = log_type

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger instance
        self.logger = self._create_logger()

    def _create_logger(self) -> logging.Logger:
        """Create and configure the logger instance."""
        # Logger name: "user.{username}.{log_type}"
        logger_name = f"user.{self.username}.{self.log_type}"
        logger = logging.getLogger(logger_name)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)
        logger.propagate = False  # Don't propagate to root logger

        # File handler
        log_filename = self.log_dir / f"{self.log_type}.log"
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Console handler (only for main log)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        if self.log_type == "main":
            logger.addHandler(console_handler)

        return logger

    def info(self, message: str):
        """Log info message."""
        self.logger.info(f"[{self.username}] {message}")

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(f"[{self.username}] {message}")

    def error(self, message: str):
        """Log error message."""
        self.logger.error(f"[{self.username}] {message}")

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(f"[{self.username}] {message}")

    def get_logger(self) -> logging.Logger:
        """Get the underlying logger instance."""
        return self.logger


def get_user_logger(username: str, log_dir: Path, log_type: str = "main") -> UserLogger:
    """
    Factory function to create or get user-specific logger.

    Args:
        username: Username
        log_dir: Log directory path
        log_type: Type of log ('main', 'scraping', 'applications')

    Returns:
        UserLogger instance
    """
    return UserLogger(username, log_dir, log_type)


# CLI testing
if __name__ == "__main__":
    from user_manager import UserManager

    manager = UserManager()
    users = manager.list_users()

    if not users:
        print("❌ No users found. Create a user first:")
        print("   python user_manager.py create testuser")
        sys.exit(1)

    # Test with first user
    test_user = users[0]
    logs_dir = manager.get_logs_dir(test_user)

    print(f"Testing logger for user: {test_user}")
    print(f"Log directory: {logs_dir}\n")

    # Create loggers
    main_logger = get_user_logger(test_user, logs_dir, "main")
    scraping_logger = get_user_logger(test_user, logs_dir, "scraping")
    app_logger = get_user_logger(test_user, logs_dir, "applications")

    # Test logging
    main_logger.info("This is a main log entry")
    main_logger.warning("This is a warning")
    main_logger.error("This is an error")

    scraping_logger.info("Starting apartment search")
    scraping_logger.info("Found 5 apartments")

    app_logger.info("Starting application bot")
    app_logger.info("Successfully applied to apartment")

    print(f"\n✅ Logs written to:")
    print(f"   {logs_dir / 'main.log'}")
    print(f"   {logs_dir / 'scraping.log'}")
    print(f"   {logs_dir / 'applications.log'}")
