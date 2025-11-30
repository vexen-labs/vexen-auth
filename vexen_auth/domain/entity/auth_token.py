"""Auth token entity for refresh tokens."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class AuthToken:
	"""
	Represents a refresh token.

	Attributes:
		id: Token ID
		user_id: ID of the user this token belongs to
		token: The refresh token value (hashed)
		expires_at: When this token expires
		created_at: When this token was created
		revoked: Whether this token has been revoked
	"""

	id: int | None
	user_id: str
	token: str  # Hashed refresh token
	expires_at: datetime
	created_at: datetime = field(default_factory=datetime.now)
	revoked: bool = False

	def is_expired(self) -> bool:
		"""Check if token is expired"""
		return datetime.now() >= self.expires_at

	def is_valid(self) -> bool:
		"""Check if token is valid (not expired and not revoked)"""
		return not self.is_expired() and not self.revoked

	def revoke(self) -> None:
		"""Revoke this token"""
		self.revoked = True

	@staticmethod
	def create_for_user(user_id: str, token: str, days_valid: int = 30) -> "AuthToken":
		"""Create a new refresh token for a user"""
		expires_at = datetime.now() + timedelta(days=days_valid)
		return AuthToken(
			id=None, user_id=user_id, token=token, expires_at=expires_at, created_at=datetime.now()
		)
