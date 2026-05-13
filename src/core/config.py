"""
Configuration Manager
"""

# ===============================================
#  IMPORTS
# ===============================================
from __future__ import annotations

# === BUILT IN ===
from pathlib import Path
from typing import Optional, TYPE_CHECKING

# === LOCAL ===
from ..services import FilesystemService
from ..models import AppConfig

if TYPE_CHECKING:
    from ..cli.ui import UI


# ===============================================
#  Config Manager
# ===============================================
class ConfigManager: pass
