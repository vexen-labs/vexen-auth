"""SQLAlchemy implementation of token repository."""

from datetime import datetime

from vexen_auth.domain.entity.auth_token import AuthToken
from vexen_auth.domain.repository.token_repository_port import ITokenRepositoryPort
from vexen_auth.infraestructure.output.persistence.sqlalchemy.mappers.auth_token_mapper import (
	AuthTokenMapper,
)
from vexen_auth.infraestructure.output.persistence.sqlalchemy.models.auth_token_model import (
	AuthTokenModel,
)

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class TokenRepository(ITokenRepositoryPort):
	"""SQLAlchemy implementation of token repository"""

	def __init__(self, session: AsyncSession):
		"""
		Initialize repository.

		Args:
			session: SQLAlchemy async session
		"""
		self.session = session

	async def save_token(self, token: AuthToken) -> AuthToken:
		"""
		Save a refresh token.

		Args:
			token: AuthToken entity

		Returns:
			Saved AuthToken with generated ID
		"""
		model = AuthTokenMapper.to_model(token)

		if model.id is None:
			# New token
			self.session.add(model)
		else:
			# Update existing
			model = await self.session.merge(model)

		await self.session.flush()
		await self.session.refresh(model)

		return AuthTokenMapper.to_entity(model)

	async def get_token_by_value(self, token_value: str) -> AuthToken | None:
		"""
		Get token by its value (hashed).

		Args:
			token_value: Hashed token value

		Returns:
			AuthToken if found, None otherwise
		"""
		stmt = select(AuthTokenModel).where(AuthTokenModel.token == token_value)
		result = await self.session.execute(stmt)
		model = result.scalar_one_or_none()

		if not model:
			return None

		return AuthTokenMapper.to_entity(model)

	async def get_tokens_by_user(self, user_id: str) -> list[AuthToken]:
		"""
		Get all tokens for a user.

		Args:
			user_id: User ID

		Returns:
			List of AuthToken entities
		"""
		stmt = select(AuthTokenModel).where(AuthTokenModel.user_id == user_id)
		result = await self.session.execute(stmt)
		models = result.scalars().all()

		return [AuthTokenMapper.to_entity(model) for model in models]

	async def revoke_token(self, token_value: str) -> None:
		"""
		Revoke a token.

		Args:
			token_value: Hashed token value
		"""
		stmt = (
			update(AuthTokenModel).where(AuthTokenModel.token == token_value).values(revoked=True)
		)
		await self.session.execute(stmt)
		await self.session.flush()

	async def revoke_all_user_tokens(self, user_id: str) -> None:
		"""
		Revoke all tokens for a user.

		Args:
			user_id: User ID
		"""
		stmt = update(AuthTokenModel).where(AuthTokenModel.user_id == user_id).values(revoked=True)
		await self.session.execute(stmt)
		await self.session.flush()

	async def cleanup_expired_tokens(self) -> int:
		"""
		Delete expired tokens.

		Returns:
			Count of deleted tokens
		"""
		now = datetime.utcnow()
		stmt = delete(AuthTokenModel).where(AuthTokenModel.expires_at < now)
		result = await self.session.execute(stmt)
		await self.session.flush()

		return result.rowcount if result.rowcount else 0
