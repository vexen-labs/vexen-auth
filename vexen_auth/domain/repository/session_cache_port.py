"""Session cache port (interface) for fast token validation and session management."""

from abc import ABC, abstractmethod
from datetime import timedelta


class ISessionCachePort(ABC):
	"""
	Interface for session cache operations.

	This port defines operations for caching session data and tokens
	in a fast in-memory store like Redis. This improves performance
	by avoiding database queries for frequently accessed token validations.
	"""

	@abstractmethod
	async def set_access_token(
		self, token_hash: str, user_data: dict, expires_in: timedelta
	) -> None:
		"""
		Cache an access token with associated user data.

		Args:
			token_hash: Hashed access token value
			user_data: User information associated with the token
			expires_in: Time until token expires
		"""
		pass

	@abstractmethod
	async def get_access_token(self, token_hash: str) -> dict | None:
		"""
		Retrieve cached access token data.

		Args:
			token_hash: Hashed access token value

		Returns:
			User data if token is cached and valid, None otherwise
		"""
		pass

	@abstractmethod
	async def revoke_access_token(self, token_hash: str) -> None:
		"""
		Revoke a cached access token.

		Args:
			token_hash: Hashed access token value
		"""
		pass

	@abstractmethod
	async def set_refresh_token(self, token_hash: str, user_id: str, expires_in: timedelta) -> None:
		"""
		Cache a refresh token.

		Args:
			token_hash: Hashed refresh token value
			user_id: ID of the user this token belongs to
			expires_in: Time until token expires
		"""
		pass

	@abstractmethod
	async def get_refresh_token(self, token_hash: str) -> str | None:
		"""
		Retrieve cached refresh token user ID.

		Args:
			token_hash: Hashed refresh token value

		Returns:
			User ID if token is cached and valid, None otherwise
		"""
		pass

	@abstractmethod
	async def revoke_refresh_token(self, token_hash: str) -> None:
		"""
		Revoke a cached refresh token.

		Args:
			token_hash: Hashed refresh token value
		"""
		pass

	@abstractmethod
	async def revoke_all_user_tokens(self, user_id: str) -> None:
		"""
		Revoke all cached tokens for a user.

		Args:
			user_id: User ID
		"""
		pass

	@abstractmethod
	async def is_token_revoked(self, token_hash: str) -> bool:
		"""
		Check if a token has been revoked.

		Args:
			token_hash: Hashed token value

		Returns:
			True if token is revoked, False otherwise
		"""
		pass

	@abstractmethod
	async def set_user_session(
		self, user_id: str, session_data: dict, expires_in: timedelta
	) -> None:
		"""
		Cache user session data.

		Args:
			user_id: User ID
			session_data: Session information to cache
			expires_in: Time until session expires
		"""
		pass

	@abstractmethod
	async def get_user_session(self, user_id: str) -> dict | None:
		"""
		Retrieve cached user session data.

		Args:
			user_id: User ID

		Returns:
			Session data if cached and valid, None otherwise
		"""
		pass

	@abstractmethod
	async def delete_user_session(self, user_id: str) -> None:
		"""
		Delete user session data.

		Args:
			user_id: User ID
		"""
		pass

	@abstractmethod
	async def close(self) -> None:
		"""Close cache connections."""
		pass
