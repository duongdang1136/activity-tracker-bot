"""
Business Logic Services Package

This package contains the core business logic of the application,
separated into different services based on responsibility.
It creates and exposes singleton instances of each service for application-wide use.

Usage:
    from services import activity_service, management_service, web_service
"""

# 1. Import các class Service từ các file module tương ứng
from .activity_service import ActivityService
from .management_service import ManagementService
from .web_service import WebService

# 2. Tạo một instance duy nhất (singleton) cho mỗi service
activity_service = ActivityService()
management_service = ManagementService()
web_service = WebService() # <<--- DÒNG NÀY CÓ THỂ ĐANG BỊ THIẾU

# 3. (Tùy chọn nhưng khuyến khích) Định nghĩa __all__ để kiểm soát
#    những gì được import khi dùng 'from services import *'
__all__ = [
    'activity_service',
    'management_service',
    'web_service'
]