"""Local authentication provider implementation."""

from datetime import datetime, timedelta

from vexen_auth.domain.entity.auth_token import AuthToken
from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort
from vexen_auth.domain.repository.auth_repository_port import IAuthRepositoryPort
from vexen_auth.domain.repository.token_repository_port import ITokenRepositoryPort
from vexen_auth.domain.repository.user_info_port import IUserInfoPort
from vexen_auth.infraestructure.security.jwt_handler import JWTHandler
from vexen_auth.infraestructure.security.password_hasher import PasswordHasher


class LocalAuthProvider(IAuthProviderPort):
	"""Local authentication provider using email/password"""

	def __init__(
		self,
		auth_repository: IAuthRepositoryPort,
		token_repository: ITokenRepositoryPort,
		user_info_repository: IUserInfoPort,
		jwt_handler: JWTHandler,
		access_token_expires: timedelta | None = None,
		refresh_token_expires: timedelta | None = None,
	):
		"""
		Initialize local auth provider.

		Args:
			auth_repository: Repository for credential operations
			token_repository: Repository for token operations
			user_info_repository: Repository for user information
			jwt_handler: JWT token handler
			access_token_expires: Access token expiration time (default: 15 minutes)
			refresh_token_expires: Refresh token expiration time (default: 30 days)
		"""
		self.auth_repository = auth_repository
		self.token_repository = token_repository
		self.user_info_repository = user_info_repository
		self.jwt_handler = jwt_handler
		self.access_token_expires = access_token_expires or timedelta(minutes=15)
		self.refresh_token_expires = refresh_token_expires or timedelta(days=30)

	async def authenticate(self, email: str, password: str) -> tuple[str, str, str] | None:
		"""
		Authenticate a user with email and password.

		Args:
			email: User email
			password: User password

		Returns:
			Tuple of (access_token, refresh_token, user_id) if successful, None otherwise
		"""
		# Get credentials
		credential = await self.auth_repository.get_credential_by_email(email)
		if not credential:
			return None

		# Verify password
		if not PasswordHasher.verify_password(password, credential.password_hash):
			return None

		# Get user info to verify user exists
		user_info = await self.user_info_repository.get_user_by_id(credential.user_id)
		if not user_info:
			return None

		# Create tokens
		token_data = {
			"sub": credential.user_id,
			"email": user_info["email"],
		}

		access_token = self.jwt_handler.create_access_token(token_data, self.access_token_expires)
		refresh_token = self.jwt_handler.create_refresh_token(
			token_data, self.refresh_token_expires
		)

		# Save refresh token (hashed)
		hashed_refresh = self.jwt_handler.hash_token(refresh_token)
		auth_token = AuthToken(
			id=None,
			user_id=credential.user_id,
			token=hashed_refresh,
			expires_at=datetime.utcnow() + self.refresh_token_expires,
		)
		await self.token_repository.save_token(auth_token)

		# Update last login
		await self.user_info_repository.update_last_login(credential.user_id, datetime.now())

		return access_token, refresh_token, credential.user_id

	async def refresh_token(self, refresh_token: str) -> str | None:
		"""
		Refresh an access token using a refresh token.

		Args:
			refresh_token: The refresh token

		Returns:
			New access token if successful, None otherwise
		"""
		# Verify refresh token
		is_valid, payload = self.jwt_handler.verify_token(refresh_token)
		if not is_valid or not payload:
			return None

		# Check token type
		if payload.get("type") != "refresh":
			return None

		# Check if token is in database and not revoked
		hashed_refresh = self.jwt_handler.hash_token(refresh_token)
		token = await self.token_repository.get_token_by_value(hashed_refresh)
		if not token or not token.is_valid():
			return None

		# Create new access token
		token_data = {
			"sub": payload["sub"],
			"email": payload["email"],
		}

		access_token = self.jwt_handler.create_access_token(token_data, self.access_token_expires)

		return access_token

	async def revoke_token(self, refresh_token: str) -> bool:
		"""
		Revoke a refresh token.

		Args:
			refresh_token: The refresh token to revoke

		Returns:
			True if successful, False otherwise
		"""
		try:
			hashed_refresh = self.jwt_handler.hash_token(refresh_token)
			await self.token_repository.revoke_token(hashed_refresh)
			return True
		except Exception:
			return False

	async def verify_access_token(self, access_token: str) -> dict | None:
		"""
		Verify and decode an access token.

		Args:
			access_token: The access token to verify

		Returns:
			Token payload if valid, None otherwise
		"""
		is_valid, payload = self.jwt_handler.verify_token(access_token)
		if not is_valid or not payload:
			return None

		# Check token type
		if payload.get("type") != "access":
			return None

		return payload
