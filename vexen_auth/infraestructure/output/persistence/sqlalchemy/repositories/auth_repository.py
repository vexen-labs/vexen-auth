"""SQLAlchemy implementation of auth repository."""

from vexen_auth.domain.entity.user_credential import UserCredential
from vexen_auth.domain.repository.auth_repository_port import IAuthRepositoryPort
from vexen_auth.infraestructure.output.persistence.sqlalchemy.mappers.user_credential_mapper import (
	UserCredentialMapper,
)
from vexen_auth.infraestructure.output.persistence.sqlalchemy.models.user_credential_model import (
	UserCredentialModel,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AuthRepository(IAuthRepositoryPort):
	"""SQLAlchemy implementation of auth repository"""

	def __init__(self, session: AsyncSession):
		"""
		Initialize repository.

		Args:
			session: SQLAlchemy async session
		"""
		self.session = session

	async def get_credential_by_user_id(self, user_id: str) -> UserCredential | None:
		"""
		Get user credential by user ID.

		Args:
			user_id: User ID

		Returns:
			UserCredential if found, None otherwise
		"""
		stmt = select(UserCredentialModel).where(UserCredentialModel.user_id == user_id)
		result = await self.session.execute(stmt)
		model = result.scalar_one_or_none()

		if not model:
			return None

		return UserCredentialMapper.to_entity(model)

	async def get_credential_by_email(self, email: str) -> UserCredential | None:
		"""
		Get user credential by email.

		Args:
			email: User email

		Returns:
			UserCredential if found, None otherwise
		"""
		# This requires joining with the user table or having a separate query
		# For now, we'll raise NotImplementedError and handle it in the adapter
		# that has access to the user repository
		raise NotImplementedError(
			"get_credential_by_email requires integration with user repository"
		)

	async def save_credential(self, credential: UserCredential) -> UserCredential:
		"""
		Save a user credential.

		Args:
			credential: UserCredential entity

		Returns:
			Saved UserCredential with generated ID
		"""
		model = UserCredentialMapper.to_model(credential)

		if model.id is None:
			# New credential
			self.session.add(model)
		else:
			# Update existing
			model = await self.session.merge(model)

		await self.session.flush()
		await self.session.refresh(model)

		return UserCredentialMapper.to_entity(model)

	async def delete_credential(self, user_id: str) -> None:
		"""
		Delete a user credential.

		Args:
			user_id: User ID
		"""
		stmt = select(UserCredentialModel).where(UserCredentialModel.user_id == user_id)
		result = await self.session.execute(stmt)
		model = result.scalar_one_or_none()

		if model:
			await self.session.delete(model)
			await self.session.flush()
