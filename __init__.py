"""
Adaptive Runtime — Tier 1 Core
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime.runtime_manager import Runtime, RuntimeResult

__all__ = ["Runtime", "RuntimeResult"]
__version__ = "0.1.0"
