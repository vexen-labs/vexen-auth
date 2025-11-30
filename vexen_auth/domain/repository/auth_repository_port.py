"""Auth repository port (interface)."""

from abc import ABC, abstractmethod

from vexen_auth.domain.entity.user_credential import UserCredential


class IAuthRepositoryPort(ABC):
	"""Interface for authentication repository"""

	@abstractmethod
	async def get_credential_by_user_id(self, user_id: str) -> UserCredential | None:
		"""Get user credentials by user ID"""
		pass

	@abstractmethod
	async def get_credential_by_email(self, email: str) -> UserCredential | None:
		"""Get user credentials by email"""
		pass

	@abstractmethod
	async def save_credential(self, credential: UserCredential) -> UserCredential:
		"""Save or update user credentials"""
		pass

	@abstractmethod
	async def delete_credential(self, user_id: str) -> None:
		"""Delete user credentials"""
		pass
