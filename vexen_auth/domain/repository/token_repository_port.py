"""Token repository port (interface)."""

from abc import ABC, abstractmethod

from vexen_auth.domain.entity.auth_token import AuthToken


class ITokenRepositoryPort(ABC):
	"""Interface for token repository"""

	@abstractmethod
	async def save_token(self, token: AuthToken) -> AuthToken:
		"""Save a refresh token"""
		pass

	@abstractmethod
	async def get_token_by_value(self, token_value: str) -> AuthToken | None:
		"""Get token by its value (hashed)"""
		pass

	@abstractmethod
	async def get_tokens_by_user(self, user_id: str) -> list[AuthToken]:
		"""Get all tokens for a user"""
		pass

	@abstractmethod
	async def revoke_token(self, token_value: str) -> None:
		"""Revoke a token"""
		pass

	@abstractmethod
	async def revoke_all_user_tokens(self, user_id: str) -> None:
		"""Revoke all tokens for a user"""
		pass

	@abstractmethod
	async def cleanup_expired_tokens(self) -> int:
		"""Delete expired tokens, returns count of deleted tokens"""
		pass
