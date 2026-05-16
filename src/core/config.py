"""
Configuration Manager
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === LOCAL ===
from ..models import AppConfig
from ..utils import LogLevel, LogTarget


# ===============================================
#  CONFIG MANAGER
# ===============================================
VALID_LOG_LEVELS = LogLevel._member_names_  # pylint:disable=E1101,W0212
VALID_LOG_TARGETS = LogTarget._member_names_  # pylint:disable=E1101,W0212


# ===============================================
#  CONFIG MANAGER
# ===============================================
class ConfigManager:
    pass
