"""Auth provider port interface."""

from abc import ABC, abstractmethod


class IAuthProviderPort(ABC):
	"""Interface for authentication providers"""

	@abstractmethod
	async def authenticate(
		self, email: str, password: str
	) -> tuple[str, str, str] | None:
		"""
		Authenticate a user with credentials.

		Args:
			email: User email
			password: User password

		Returns:
			Tuple of (access_token, refresh_token, user_id) if successful, None otherwise
		"""
		pass

	@abstractmethod
	async def refresh_token(self, refresh_token: str) -> str | None:
		"""
		Refresh an access token using a refresh token.

		Args:
			refresh_token: The refresh token

		Returns:
			New access token if successful, None otherwise
		"""
		pass

	@abstractmethod
	async def revoke_token(self, refresh_token: str) -> bool:
		"""
		Revoke a refresh token.

		Args:
			refresh_token: The refresh token to revoke

		Returns:
			True if successful, False otherwise
		"""
		pass

	@abstractmethod
	async def verify_access_token(self, access_token: str) -> dict | None:
		"""
		Verify and decode an access token.

		Args:
			access_token: The access token to verify

		Returns:
			Token payload if valid, None otherwise
		"""
		pass
