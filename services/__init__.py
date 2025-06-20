"""
Business Logic Services Package

This package contains the core business logic of the application,
separated into different services based on responsibility.

Usage:
    from services import activity_service, management_service
"""

# Import and expose an instance of ActivityService
from .activity_service import ActivityService
activity_service = ActivityService()

# Import and expose an instance of ManagementService
from .management_service import ManagementService
management_service = ManagementService()

# Import and expose an instance of WebService
from .web_service import WebService
web_service = WebService()

__all__ = [
    'activity_service',
    'management_service',
    'web_service'
]