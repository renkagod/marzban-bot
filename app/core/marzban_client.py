from marzban import MarzbanAPI, UserCreate, UserModify
import logging

logger = logging.getLogger(__name__)

class MarzbanManager:
    def __init__(self, address: str, username: str = None, password: str = None):
        # Используем base_url вместо address
        self.client = MarzbanAPI(base_url=address)
        self.username = username
        self.password = password
        self.token = None

    async def _ensure_token(self):
        """Получает токен, если он еще не получен."""
        if not self.token and self.username and self.password:
            token_obj = await self.client.get_token(self.username, self.password)
            self.token = token_obj.access_token if hasattr(token_obj, 'access_token') else token_obj

    async def check_connectivity(self) -> bool:
        """Проверяет связь с API."""
        try:
            await self._ensure_token()
            await self.client.get_system_stats(token=self.token)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Marzban API: {e}")
            return False

    async def get_stats(self):
        """Возвращает статистику сервера."""
        await self._ensure_token()
        return await self.client.get_system_stats(token=self.token)

    async def get_user(self, username: str):
        """Возвращает информацию о пользователе."""
        await self._ensure_token()
        return await self.client.get_user(username, token=self.token)

    async def create_user(self, user_dict: dict):
        """Создает пользователя."""
        await self._ensure_token()
        # Превращаем словарь в объект UserCreate
        user_obj = UserCreate(**user_dict)
        return await self.client.add_user(user_obj, token=self.token)

    async def modify_user(self, username: str, user_dict: dict):
        """Изменяет данные пользователя (например, продление)."""
        await self._ensure_token()
        # Превращаем словарь в объект UserModify
        user_obj = UserModify(**user_dict)
        return await self.client.modify_user(username, user_obj, token=self.token)
