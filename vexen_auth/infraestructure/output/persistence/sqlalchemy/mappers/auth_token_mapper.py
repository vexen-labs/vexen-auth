"""Mapper for AuthToken entity and model."""

from vexen_auth.domain.entity.auth_token import AuthToken
from vexen_auth.infraestructure.output.persistence.sqlalchemy.models.auth_token_model import (
	AuthTokenModel,
)


class AuthTokenMapper:
	"""Maps between AuthToken entity and AuthTokenModel"""

	@staticmethod
	def to_entity(model: AuthTokenModel) -> AuthToken:
		"""
		Convert model to entity.

		Args:
			model: AuthTokenModel instance

		Returns:
			AuthToken entity
		"""
		return AuthToken(
			id=model.id,
			user_id=model.user_id,
			token=model.token,
			expires_at=model.expires_at,
			created_at=model.created_at,
			revoked=model.revoked,
		)

	@staticmethod
	def to_model(entity: AuthToken) -> AuthTokenModel:
		"""
		Convert entity to model.

		Args:
			entity: AuthToken entity

		Returns:
			AuthTokenModel instance
		"""
		return AuthTokenModel(
			id=entity.id,
			user_id=entity.user_id,
			token=entity.token,
			expires_at=entity.expires_at,
			created_at=entity.created_at,
			revoked=entity.revoked,
		)
