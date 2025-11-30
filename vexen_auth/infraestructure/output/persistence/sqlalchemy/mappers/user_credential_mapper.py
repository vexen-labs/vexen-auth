"""Mapper for UserCredential entity and model."""

from vexen_auth.domain.entity.user_credential import UserCredential
from vexen_auth.infraestructure.output.persistence.sqlalchemy.models.user_credential_model import (
	UserCredentialModel,
)


class UserCredentialMapper:
	"""Maps between UserCredential entity and UserCredentialModel"""

	@staticmethod
	def to_entity(model: UserCredentialModel) -> UserCredential:
		"""
		Convert model to entity.

		Args:
			model: UserCredentialModel instance

		Returns:
			UserCredential entity
		"""
		return UserCredential(
			id=model.id,
			user_id=model.user_id,
			password_hash=model.password_hash,
			created_at=model.created_at,
			updated_at=model.updated_at,
		)

	@staticmethod
	def to_model(entity: UserCredential) -> UserCredentialModel:
		"""
		Convert entity to model.

		Args:
			entity: UserCredential entity

		Returns:
			UserCredentialModel instance
		"""
		return UserCredentialModel(
			id=entity.id,
			user_id=entity.user_id,
			password_hash=entity.password_hash,
			created_at=entity.created_at,
			updated_at=entity.updated_at,
		)
