"""Adapter for user information from vexen-user."""

from datetime import datetime

from vexen_auth.domain.repository.user_info_port import IUserInfoPort


class UserInfoAdapter(IUserInfoPort):
	"""
	Adapter for retrieving user information.

	This adapter can be configured to use either:
	- Direct database access (via injected SQLAlchemy repository)
	- External service calls (via injected vexen-user service)
	"""

	def __init__(self, user_service=None, user_repository=None):
		"""
		Initialize user info adapter.

		Args:
			user_service: Optional VexenUser service instance
			user_repository: Optional SQLAlchemy user repository
		"""
		self.user_service = user_service
		self.user_repository = user_repository

		if not user_service and not user_repository:
			raise ValueError("Either user_service or user_repository must be provided")

	async def get_user_by_id(self, user_id: str) -> dict | None:
		"""
		Get user information by ID.

		Args:
			user_id: User ID

		Returns:
			Dictionary with user info or None if not found
		"""
		if self.user_service:
			# Use VexenUser service
			user = await self.user_service.service.get(user_id)
			if not user:
				return None

			return {
				"id": user.id,
				"email": user.email,
				"name": user.name,
				"avatar": user.avatar,
				"created_at": user.created_at,
				"last_login": user.last_login,
			}

		# Use direct repository access
		user = await self.user_repository.get_by_id(user_id)
		if not user:
			return None

		return {
			"id": user.id,
			"email": user.email,
			"name": user.name,
			"avatar": user.avatar,
			"role_id": user.role_id,
			"created_at": user.created_at,
			"last_login": user.last_login,
		}

	async def get_user_by_email(self, email: str) -> dict | None:
		"""
		Get user information by email.

		Args:
			email: User email

		Returns:
			Dictionary with user info or None if not found
		"""
		if self.user_repository:
			# Use direct repository access
			user = await self.user_repository.get_by_email(email)
			if not user:
				return None

			return {
				"id": user.id,
				"email": user.email,
				"name": user.name,
				"avatar": user.avatar,
				"created_at": user.created_at,
				"last_login": user.last_login,
			}

		raise NotImplementedError("get_user_by_email requires direct repository access")

	async def update_last_login(self, user_id: str, timestamp: datetime) -> None:
		"""
		Update user's last login timestamp.

		Args:
			user_id: User ID
			timestamp: Login timestamp
		"""
		if self.user_repository:
			await self.user_repository.update_last_login(user_id, timestamp)
		else:
			# If using service, we might need to patch the user
			# This depends on the vexen-user API implementation
			raise NotImplementedError("update_last_login via service not implemented yet")
