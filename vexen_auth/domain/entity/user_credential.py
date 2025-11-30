"""User credential entity for password storage."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserCredential:
	"""
	Represents user authentication credentials.

	Attributes:
		id: Credential ID
		user_id: ID of the user
		password_hash: Hashed password
		created_at: When credentials were created
		updated_at: When credentials were last updated
	"""

	id: int | None
	user_id: str
	password_hash: str
	created_at: datetime = field(default_factory=datetime.now)
	updated_at: datetime | None = None

	def update_password(self, new_password_hash: str) -> None:
		"""Update the password hash"""
		self.password_hash = new_password_hash
		self.updated_at = datetime.now()
