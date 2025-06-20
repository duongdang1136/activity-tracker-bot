"""
External APIs Package

This package contains wrappers for all external service APIs (Discord, Zalo, etc.).
It exposes singleton instances of each API client for application-wide use.

Usage:
    from api import zalo_api_client, discord_api_client
"""
from .zalo_api import zalo_api_client
from .discord_api import DiscordApiClient 
from .telegram_api import telegram_api_client
from .base_client import BaseApiClient


__all__ = [
    'zalo_api_client',
    'DiscordApiClient',
    'BaseApiClient',
    'telegram_api_client'
]