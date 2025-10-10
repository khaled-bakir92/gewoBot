#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Manager - Multi-User Support for Gewobag Bot
==================================================

Manages multiple users with separate:
- Configuration files (user_data.json, filter_config.json)
- Browser sessions (cookies, local storage)
- Log files
- Browser fingerprints

Author: Gewobag Bot Team
Version: 2.1
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Base directories
BASE_DIR = Path(__file__).parent.resolve()
USERS_DIR = BASE_DIR / "users"

# Ensure users directory exists
USERS_DIR.mkdir(exist_ok=True)

# Logger
logger = logging.getLogger(__name__)


class UserManager:
    """Manages user profiles and their configurations."""

    def __init__(self):
        self.users_dir = USERS_DIR
        self.users_dir.mkdir(exist_ok=True)

    def create_user(self, username: str) -> bool:
        """
        Create a new user profile with directory structure.

        Args:
            username: User identifier (e.g., 'user1', 'maria', 'john')

        Returns:
            True if user created successfully, False if already exists
        """
        user_dir = self.users_dir / username

        if user_dir.exists():
            logger.warning(f"⚠️  User '{username}' already exists!")
            return False

        # Create user directory structure
        user_dir.mkdir(parents=True)
        (user_dir / "cookies").mkdir()
        (user_dir / "logs").mkdir()

        # Create template configuration files
        self._create_user_data_template(user_dir)
        self._create_filter_config_template(user_dir)

        logger.info(f"✅ User '{username}' created successfully!")
        logger.info(f"📁 Directory: {user_dir}")
        logger.info(f"📝 Please edit: {user_dir / 'user_data.json'}")

        return True

    def _create_user_data_template(self, user_dir: Path) -> None:
        """Create user_data.json template."""
        template = {
            "personal_info": {
                "anrede": "Herr",
                "vorname": "Ihr Vorname",
                "nachname": "Ihr Nachname",
                "email": "ihre.email@example.com",
                "telefon": "+49 123 456789",
                "geburtsdatum": "01.01.1990",
                "staatsangehoerigkeit": "Deutsch"
            },
            "household": {
                "anzahl_personen": 1,
                "haushaltseinkommen": "3000"
            },
            "documents": {
                "personalausweis": "/absoluter/pfad/zu/personalausweis.pdf",
                "gehaltsnachweis_1": "/absoluter/pfad/zu/gehaltsnachweis1.pdf",
                "gehaltsnachweis_2": "/absoluter/pfad/zu/gehaltsnachweis2.pdf",
                "gehaltsnachweis_3": "/absoluter/pfad/zu/gehaltsnachweis3.pdf",
                "schufa": "/absoluter/pfad/zu/schufa.pdf",
                "mietschuldenfreiheit": "/absoluter/pfad/zu/mietschuldenfreiheit.pdf"
            },
            "nachricht": "Sehr geehrte Damen und Herren,\\n\\nhiermit bewerbe ich mich um die ausgeschriebene Wohnung.\\n\\nMit freundlichen Grüßen"
        }

        filepath = user_dir / "user_data.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Created: {filepath}")

    def _create_filter_config_template(self, user_dir: Path) -> None:
        """Create filter_config.json template."""
        template = {
            "gewuenschte_bezirke": [
                "friedrichshain-kreuzberg",
                "mitte",
                "pankow-prenzlauer-berg"
            ],
            "gesamtmiete_von": "800",
            "gesamtmiete_bis": "1500",
            "gesamtflaeche_von": "60",
            "gesamtflaeche_bis": "100",
            "zimmer_von": "2",
            "zimmer_bis": "4",
            "wbs": ""
        }

        filepath = user_dir / "filter_config.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Created: {filepath}")

    def list_users(self) -> List[str]:
        """
        List all existing users.

        Returns:
            List of usernames
        """
        if not self.users_dir.exists():
            return []

        users = [
            d.name for d in self.users_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]
        return sorted(users)

    def user_exists(self, username: str) -> bool:
        """Check if user exists."""
        return (self.users_dir / username).exists()

    def get_user_dir(self, username: str) -> Path:
        """Get user's directory path."""
        return self.users_dir / username

    def get_user_data_path(self, username: str) -> Path:
        """Get path to user's user_data.json."""
        return self.get_user_dir(username) / "user_data.json"

    def get_filter_config_path(self, username: str) -> Path:
        """Get path to user's filter_config.json."""
        return self.get_user_dir(username) / "filter_config.json"

    def get_cookies_dir(self, username: str) -> Path:
        """Get path to user's cookies directory."""
        return self.get_user_dir(username) / "cookies"

    def get_logs_dir(self, username: str) -> Path:
        """Get path to user's logs directory."""
        return self.get_user_dir(username) / "logs"

    def validate_user_config(self, username: str) -> Dict[str, Any]:
        """
        Validate user's configuration files.

        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Check if user exists
        if not self.user_exists(username):
            result["valid"] = False
            result["errors"].append(f"User '{username}' does not exist")
            return result

        # Check user_data.json
        user_data_path = self.get_user_data_path(username)
        if not user_data_path.exists():
            result["valid"] = False
            result["errors"].append(f"Missing: {user_data_path}")
        else:
            try:
                with open(user_data_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)

                # Check required fields
                if "personal_info" not in user_data:
                    result["errors"].append("Missing 'personal_info' in user_data.json")
                    result["valid"] = False
                else:
                    required_fields = ["vorname", "nachname", "email"]
                    for field in required_fields:
                        if field not in user_data["personal_info"]:
                            result["errors"].append(f"Missing field: personal_info.{field}")
                            result["valid"] = False
                        elif "Ihr" in str(user_data["personal_info"].get(field, "")):
                            result["warnings"].append(f"Template value in: personal_info.{field}")

                # Check documents
                if "documents" in user_data:
                    for doc_name, doc_path in user_data["documents"].items():
                        if doc_path and not doc_path.startswith("/absoluter/pfad"):
                            if not Path(doc_path).exists():
                                result["warnings"].append(f"Document not found: {doc_name} → {doc_path}")

            except json.JSONDecodeError:
                result["valid"] = False
                result["errors"].append(f"Invalid JSON: {user_data_path}")

        # Check filter_config.json
        filter_config_path = self.get_filter_config_path(username)
        if not filter_config_path.exists():
            result["warnings"].append(f"Missing: {filter_config_path} (will use defaults)")
        else:
            try:
                with open(filter_config_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                result["valid"] = False
                result["errors"].append(f"Invalid JSON: {filter_config_path}")

        return result

    def load_user_data(self, username: str) -> Dict[str, Any]:
        """Load user's user_data.json."""
        path = self.get_user_data_path(username)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_filter_config(self, username: str) -> Dict[str, Any]:
        """Load user's filter_config.json."""
        path = self.get_filter_config_path(username)
        if not path.exists():
            logger.warning(f"⚠️  No filter config for user '{username}', using defaults")
            return {}

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get comprehensive user information."""
        if not self.user_exists(username):
            return {"exists": False}

        user_dir = self.get_user_dir(username)
        validation = self.validate_user_config(username)

        return {
            "exists": True,
            "username": username,
            "directory": str(user_dir),
            "user_data_path": str(self.get_user_data_path(username)),
            "filter_config_path": str(self.get_filter_config_path(username)),
            "cookies_dir": str(self.get_cookies_dir(username)),
            "logs_dir": str(self.get_logs_dir(username)),
            "validation": validation
        }

    def delete_user(self, username: str, confirm: bool = False) -> bool:
        """
        Delete a user profile (with confirmation).

        Args:
            username: User to delete
            confirm: Must be True to actually delete

        Returns:
            True if deleted, False otherwise
        """
        if not confirm:
            logger.warning("⚠️  Delete requires confirm=True parameter")
            return False

        user_dir = self.get_user_dir(username)
        if not user_dir.exists():
            logger.warning(f"⚠️  User '{username}' does not exist")
            return False

        import shutil
        shutil.rmtree(user_dir)
        logger.info(f"🗑️  User '{username}' deleted: {user_dir}")
        return True


def print_user_list():
    """Pretty-print list of users."""
    manager = UserManager()
    users = manager.list_users()

    if not users:
        print("📭 No users found. Create one with: python main.py --create-user <username>")
        return

    print(f"\n👥 Found {len(users)} user(s):\n")

    for username in users:
        info = manager.get_user_info(username)
        validation = info["validation"]

        status_icon = "✅" if validation["valid"] else "❌"
        print(f"{status_icon} {username}")
        print(f"   📁 {info['directory']}")

        if validation["errors"]:
            for error in validation["errors"]:
                print(f"   ❌ {error}")

        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"   ⚠️  {warning}")

        print()


def print_user_info(username: str):
    """Pretty-print user information."""
    manager = UserManager()
    info = manager.get_user_info(username)

    if not info["exists"]:
        print(f"❌ User '{username}' does not exist")
        print(f"💡 Create with: python main.py --create-user {username}")
        return

    validation = info["validation"]
    status_icon = "✅" if validation["valid"] else "❌"

    print(f"\n{status_icon} User: {username}\n")
    print(f"📁 Directory: {info['directory']}")
    print(f"📄 User Data: {info['user_data_path']}")
    print(f"🔍 Filters: {info['filter_config_path']}")
    print(f"🍪 Cookies: {info['cookies_dir']}")
    print(f"📊 Logs: {info['logs_dir']}")

    print(f"\n{'='*60}")
    print("VALIDATION RESULTS")
    print(f"{'='*60}\n")

    if validation["valid"]:
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has errors:")
        for error in validation["errors"]:
            print(f"   • {error}")

    if validation["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in validation["warnings"]:
            print(f"   • {warning}")

    print()


# CLI usage
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    manager = UserManager()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python user_manager.py create <username>")
        print("  python user_manager.py list")
        print("  python user_manager.py info <username>")
        print("  python user_manager.py validate <username>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create" and len(sys.argv) == 3:
        username = sys.argv[2]
        manager.create_user(username)

    elif command == "list":
        print_user_list()

    elif command == "info" and len(sys.argv) == 3:
        username = sys.argv[2]
        print_user_info(username)

    elif command == "validate" and len(sys.argv) == 3:
        username = sys.argv[2]
        result = manager.validate_user_config(username)
        print(json.dumps(result, indent=2))

    else:
        print("❌ Invalid command or arguments")
        sys.exit(1)
