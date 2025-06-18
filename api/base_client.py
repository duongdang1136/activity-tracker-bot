# api/base_client.py (File mới)
from abc import ABC, abstractmethod

class BaseApiClient(ABC):
    @abstractmethod
    def send_message(self, group_id: str, message: str):
        pass

    @abstractmethod
    def remove_user(self, group_id: str, user_id: str):
        pass