#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Fingerprint Pool - Unique Fingerprints per User
========================================================

Generates and manages unique browser fingerprints for each user:
- User-Agent (from pool of 20 realistic agents)
- Viewport size (randomized per user)
- Geolocation (Berlin with small variations)
- Platform and hardware concurrency

Author: Gewobag Bot Team
Version: 2.1
"""

import json
import random
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Any
from dataclasses import dataclass, asdict

# User-Agent Pool (realistic Chrome, Firefox, Safari, Edge)
USER_AGENT_POOL = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",

    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",

    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",

    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",

    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",

    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

# Viewport sizes (width, height)
VIEWPORT_POOL = [
    (1920, 1080),
    (1920, 1200),
    (1680, 1050),
    (1600, 900),
    (1536, 864),
    (1440, 900),
    (1366, 768),
    (2560, 1440),
    (2560, 1600),
    (1280, 720),
]

# Berlin coordinates with small variations
BERLIN_BASE_LAT = 52.520008
BERLIN_BASE_LON = 13.404954


@dataclass
class BrowserFingerprint:
    """Browser fingerprint configuration for a user."""
    user_agent: str
    viewport_width: int
    viewport_height: int
    latitude: float
    longitude: float
    locale: str = "de-DE"
    timezone: str = "Europe/Berlin"
    platform: str = "Win32"
    hardware_concurrency: int = 8
    device_memory: int = 8


class FingerprintManager:
    """Manages browser fingerprints for users."""

    def __init__(self, users_dir: Path):
        self.users_dir = users_dir

    def _get_fingerprint_path(self, username: str) -> Path:
        """Get path to user's fingerprint config file."""
        return self.users_dir / username / "fingerprint.json"

    def _generate_deterministic_fingerprint(self, username: str) -> BrowserFingerprint:
        """
        Generate a deterministic fingerprint based on username.

        Same username always gets the same fingerprint (but unique across users).
        """
        # Use username hash as seed for deterministic randomization
        seed = int(hashlib.md5(username.encode()).hexdigest(), 16)
        rng = random.Random(seed)

        # Select user agent
        user_agent = rng.choice(USER_AGENT_POOL)

        # Select viewport
        viewport = rng.choice(VIEWPORT_POOL)

        # Generate Berlin coordinates with small variation (±0.02 degrees ≈ ±2km)
        latitude = BERLIN_BASE_LAT + rng.uniform(-0.02, 0.02)
        longitude = BERLIN_BASE_LON + rng.uniform(-0.02, 0.02)

        # Determine platform from user agent
        if "Windows" in user_agent:
            platform = "Win32"
        elif "Macintosh" in user_agent:
            platform = "MacIntel"
        elif "Linux" in user_agent:
            platform = "Linux x86_64"
        else:
            platform = "Win32"

        # Randomize hardware specs slightly
        hardware_concurrency = rng.choice([4, 8, 12, 16])
        device_memory = rng.choice([4, 8, 16, 32])

        return BrowserFingerprint(
            user_agent=user_agent,
            viewport_width=viewport[0],
            viewport_height=viewport[1],
            latitude=round(latitude, 6),
            longitude=round(longitude, 6),
            locale="de-DE",
            timezone="Europe/Berlin",
            platform=platform,
            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory
        )

    def get_or_create_fingerprint(self, username: str) -> BrowserFingerprint:
        """
        Get existing fingerprint or create new one for user.

        Fingerprints are persistent - same user always gets the same fingerprint.
        """
        fingerprint_path = self._get_fingerprint_path(username)

        # Load existing fingerprint
        if fingerprint_path.exists():
            with open(fingerprint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return BrowserFingerprint(**data)

        # Generate new fingerprint
        fingerprint = self._generate_deterministic_fingerprint(username)

        # Save for future use
        fingerprint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(fingerprint_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(fingerprint), f, indent=2)

        return fingerprint

    def get_playwright_config(self, username: str) -> Dict[str, Any]:
        """
        Get Playwright browser context configuration for user.

        Returns:
            Dictionary with Playwright browser_context settings
        """
        fingerprint = self.get_or_create_fingerprint(username)

        return {
            "user_agent": fingerprint.user_agent,
            "viewport": {
                "width": fingerprint.viewport_width,
                "height": fingerprint.viewport_height
            },
            "geolocation": {
                "latitude": fingerprint.latitude,
                "longitude": fingerprint.longitude
            },
            "permissions": ["geolocation"],
            "locale": fingerprint.locale,
            "timezone_id": fingerprint.timezone,
            # Additional stealth settings
            "ignore_https_errors": True,
            "java_script_enabled": True,
        }

    def regenerate_fingerprint(self, username: str) -> BrowserFingerprint:
        """
        Regenerate fingerprint for user (useful if user is blocked/detected).

        Deletes old fingerprint and creates a new random one.
        """
        fingerprint_path = self._get_fingerprint_path(username)

        if fingerprint_path.exists():
            fingerprint_path.unlink()

        # Generate new fingerprint with additional random suffix
        import time
        modified_username = f"{username}_{int(time.time())}"
        fingerprint = self._generate_deterministic_fingerprint(modified_username)

        # Save with original username
        with open(fingerprint_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(fingerprint), f, indent=2)

        return fingerprint

    def print_fingerprint(self, username: str) -> None:
        """Pretty-print user's fingerprint."""
        fingerprint = self.get_or_create_fingerprint(username)

        print(f"\n{'='*60}")
        print(f"Browser Fingerprint: {username}")
        print(f"{'='*60}\n")

        print(f"🌐 User-Agent:")
        print(f"   {fingerprint.user_agent}\n")

        print(f"📺 Viewport: {fingerprint.viewport_width}x{fingerprint.viewport_height}")
        print(f"📍 Location: {fingerprint.latitude}, {fingerprint.longitude} (Berlin)")
        print(f"🌍 Locale: {fingerprint.locale}")
        print(f"🕐 Timezone: {fingerprint.timezone}")
        print(f"💻 Platform: {fingerprint.platform}")
        print(f"⚙️  CPU Cores: {fingerprint.hardware_concurrency}")
        print(f"🧠 Memory: {fingerprint.device_memory} GB")
        print()


# CLI usage
if __name__ == "__main__":
    import sys
    from user_manager import USERS_DIR

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python fingerprint_pool.py show <username>")
        print("  python fingerprint_pool.py regenerate <username>")
        sys.exit(1)

    command = sys.argv[1]
    username = sys.argv[2]

    manager = FingerprintManager(USERS_DIR)

    if command == "show":
        manager.print_fingerprint(username)

    elif command == "regenerate":
        print(f"🔄 Regenerating fingerprint for '{username}'...")
        fingerprint = manager.regenerate_fingerprint(username)
        print("✅ New fingerprint generated!")
        manager.print_fingerprint(username)

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
