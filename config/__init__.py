"""
Configuration Package

This package initializes and exposes the application's configuration settings
and the primary database manager instance.

Usage:
    from config import settings, db_manager
"""

# Import and expose the global settings object
from .config import settings

# Import and expose the global database manager instance
from .database import db_manager


# You can define what is exposed when someone does 'from config import *'
__all__ = [
    'settings',
    'db_manager'
]