"""Port for retrieving user information."""

from abc import ABC, abstractmethod
from datetime import datetime


class IUserInfoPort(ABC):
	"""Interface for retrieving user information"""

	@abstractmethod
	async def get_user_by_id(self, user_id: str) -> dict | None:
		"""
		Get user information by ID.

		Args:
			user_id: User ID

		Returns:
			Dictionary with user info (id, email, name, avatar, created_at, last_login)
			or None if not found
		"""
		pass

	@abstractmethod
	async def get_user_by_email(self, email: str) -> dict | None:
		"""
		Get user information by email.

		Args:
			email: User email

		Returns:
			Dictionary with user info (id, email, name, avatar, created_at, last_login)
			or None if not found
		"""
		pass

	@abstractmethod
	async def update_last_login(self, user_id: str, timestamp: datetime) -> None:
		"""
		Update user's last login timestamp.

		Args:
			user_id: User ID
			timestamp: Login timestamp
		"""
		pass
