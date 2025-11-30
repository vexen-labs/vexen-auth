"""Enhanced auth repository adapter with user integration."""

from vexen_auth.domain.entity.user_credential import UserCredential
from vexen_auth.domain.repository.auth_repository_port import IAuthRepositoryPort
from vexen_auth.domain.repository.user_info_port import IUserInfoPort
from vexen_auth.infraestructure.output.persistence.sqlalchemy.repositories.auth_repository import (
	AuthRepository,
)


class AuthRepositoryAdapter(IAuthRepositoryPort):
	"""
	Enhanced auth repository that can query by email.

	This adapter wraps the base AuthRepository and adds
	user integration for email-based queries.
	"""

	def __init__(self, auth_repository: AuthRepository, user_info_port: IUserInfoPort):
		"""
		Initialize adapter.

		Args:
			auth_repository: Base auth repository
			user_info_port: User info port for email lookups
		"""
		self.auth_repository = auth_repository
		self.user_info_port = user_info_port

	async def get_credential_by_user_id(self, user_id: str) -> UserCredential | None:
		"""
		Get user credential by user ID.

		Args:
			user_id: User ID

		Returns:
			UserCredential if found, None otherwise
		"""
		return await self.auth_repository.get_credential_by_user_id(user_id)

	async def get_credential_by_email(self, email: str) -> UserCredential | None:
		"""
		Get user credential by email.

		Args:
			email: User email

		Returns:
			UserCredential if found, None otherwise
		"""
		# Get user by email
		user = await self.user_info_port.get_user_by_email(email)
		if not user:
			return None

		# Get credential by user_id
		return await self.auth_repository.get_credential_by_user_id(user["id"])

	async def save_credential(self, credential: UserCredential) -> UserCredential:
		"""
		Save a user credential.

		Args:
			credential: UserCredential entity

		Returns:
			Saved UserCredential with generated ID
		"""
		return await self.auth_repository.save_credential(credential)

	async def delete_credential(self, user_id: str) -> None:
		"""
		Delete a user credential.

		Args:
			user_id: User ID
		"""
		await self.auth_repository.delete_credential(user_id)
