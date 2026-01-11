from marzban import MarzbanAPI
import logging

logger = logging.getLogger(__name__)

class MarzbanManager:
    def __init__(self, address: str, username: str = None, password: str = None):
        self.client = MarzbanAPI(
            address=address,
            username=username,
            password=password
        )

    def check_connectivity(self) -> bool:
        """
        Checks connectivity by attempting to get system stats.
        Returns True if successful, False otherwise.
        """
        try:
            self.client.get_system_stats()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Marzban API: {e}")
            return False

    def get_stats(self):
        """Returns server stats."""
        return self.client.get_system_stats()

    def get_user(self, username: str):
        """Returns user information from Marzban."""
        return self.client.get_user(username)

    def create_user(self, user_dict: dict):
        """Creates a user in Marzban."""
        # Using add_user from MarzbanAPI
        return self.client.add_user(user_dict)