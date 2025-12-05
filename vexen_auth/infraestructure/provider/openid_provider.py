"""OpenID Connect authentication provider implementation."""

from datetime import datetime, timedelta
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import JsonWebKey, jwt

from vexen_auth.domain.entity.auth_token import AuthToken
from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort
from vexen_auth.domain.repository.auth_repository_port import IAuthRepositoryPort
from vexen_auth.domain.repository.session_cache_port import ISessionCachePort
from vexen_auth.domain.repository.token_repository_port import ITokenRepositoryPort
from vexen_auth.domain.repository.user_info_port import IUserInfoPort
from vexen_auth.infraestructure.security.jwt_handler import JWTHandler


class OpenIDProvider(IAuthProviderPort):
	"""
	OpenID Connect authentication provider.

	Supports standard OpenID Connect providers like:
	- Google
	- Azure AD / Microsoft Entra ID
	- Keycloak
	- Auth0
	- Okta
	- And any OpenID Connect compliant provider
	"""

	def __init__(
		self,
		client_id: str,
		client_secret: str,
		discovery_url: str,
		redirect_uri: str,
		token_repository: ITokenRepositoryPort,
		user_info_repository: IUserInfoPort,
		jwt_handler: JWTHandler,
		auth_repository: IAuthRepositoryPort | None = None,
		access_token_expires: timedelta | None = None,
		refresh_token_expires: timedelta | None = None,
		session_cache: ISessionCachePort | None = None,
		scopes: list[str] | None = None,
	):
		"""
		Initialize OpenID Connect provider.

		Args:
			client_id: OAuth2 client ID
			client_secret: OAuth2 client secret
			discovery_url: OpenID Connect discovery URL (e.g., https://accounts.google.com/.well-known/openid-configuration)
			redirect_uri: OAuth2 redirect URI
			token_repository: Repository for token operations
			user_info_repository: Repository for user information
			jwt_handler: JWT token handler for internal tokens
			auth_repository: Optional repository for credential operations
			access_token_expires: Internal access token expiration time (default: 15 minutes)
			refresh_token_expires: Internal refresh token expiration time (default: 30 days)
			session_cache: Optional session cache (Redis) for improved performance
			scopes: OAuth2 scopes (default: ["openid", "email", "profile"])
		"""
		self.client_id = client_id
		self.client_secret = client_secret
		self.discovery_url = discovery_url
		self.redirect_uri = redirect_uri
		self.token_repository = token_repository
		self.user_info_repository = user_info_repository
		self.jwt_handler = jwt_handler
		self.auth_repository = auth_repository
		self.session_cache = session_cache
		self.access_token_expires = access_token_expires or timedelta(minutes=15)
		self.refresh_token_expires = refresh_token_expires or timedelta(days=30)
		self.scopes = scopes or ["openid", "email", "profile"]

		# OpenID Connect configuration (will be loaded from discovery URL)
		self._oidc_config: dict[str, Any] | None = None
		self._jwks: JsonWebKey | None = None

	async def _load_oidc_config(self) -> None:
		"""Load OpenID Connect configuration from discovery URL."""
		if self._oidc_config is not None:
			return

		async with httpx.AsyncClient() as client:
			response = await client.get(self.discovery_url)
			response.raise_for_status()
			self._oidc_config = response.json()

			# Load JWKS for token verification
			jwks_uri = self._oidc_config["jwks_uri"]
			jwks_response = await client.get(jwks_uri)
			jwks_response.raise_for_status()
			self._jwks = JsonWebKey.import_key_set(jwks_response.json())

	def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
		"""
		Get the authorization URL for OAuth2 flow.

		Args:
			state: Optional state parameter for CSRF protection

		Returns:
			Tuple of (authorization_url, state)
		"""
		if self._oidc_config is None:
			raise RuntimeError("OpenID configuration not loaded. Call authenticate first.")

		client = AsyncOAuth2Client(
			client_id=self.client_id,
			client_secret=self.client_secret,
			redirect_uri=self.redirect_uri,
			scope=" ".join(self.scopes),
		)

		authorization_endpoint = self._oidc_config["authorization_endpoint"]
		return client.create_authorization_url(authorization_endpoint, state=state)

	async def exchange_code(self, code: str) -> dict[str, Any] | None:
		"""
		Exchange authorization code for tokens.

		Args:
			code: Authorization code from OAuth2 callback

		Returns:
			Token response containing access_token, id_token, etc.
		"""
		await self._load_oidc_config()

		client = AsyncOAuth2Client(
			client_id=self.client_id,
			client_secret=self.client_secret,
			redirect_uri=self.redirect_uri,
		)

		token_endpoint = self._oidc_config["token_endpoint"]
		token_response = await client.fetch_token(token_endpoint, code=code)

		return token_response

	async def verify_id_token(self, id_token: str) -> dict[str, Any] | None:
		"""
		Verify and decode OpenID Connect ID token.

		Args:
			id_token: The ID token to verify

		Returns:
			Token payload if valid, None otherwise
		"""
		if self._jwks is None:
			await self._load_oidc_config()

		try:
			claims = jwt.decode(id_token, self._jwks)
			claims.validate()
			return claims
		except Exception:
			return None

	async def authenticate_with_code(
		self, code: str
	) -> tuple[str, str, str, dict[str, Any]] | None:
		"""
		Authenticate using authorization code and return internal tokens.

		Args:
			code: Authorization code from OAuth2 callback

		Returns:
			Tuple of (access_token, refresh_token, user_id, user_info) if successful, None otherwise
		"""
		# Exchange code for tokens
		token_response = await self.exchange_code(code)
		if not token_response:
			return None

		# Verify ID token
		id_token = token_response.get("id_token")
		if not id_token:
			return None

		claims = await self.verify_id_token(id_token)
		if not claims:
			return None

		# Extract user information
		email = claims.get("email")
		name = claims.get("name") or claims.get("preferred_username")
		sub = claims.get("sub")  # OpenID subject (unique user ID from provider)

		if not email or not sub:
			return None

		# Check if user exists, create if not
		user_info = await self.user_info_repository.get_user_by_email(email)

		if not user_info:
			# Create new user with OpenID provider info
			user_data = {
				"email": email,
				"name": name or email.split("@")[0],
				"status": "active",
				"user_metadata": {
					"auth_provider": "openid",
					"openid_sub": sub,
					"openid_issuer": claims.get("iss"),
				},
			}

			# This would need to call user creation - implementation depends on integration
			# For now, return None if user doesn't exist
			# TODO: Integrate with user creation service
			return None

		user_id = user_info["id"]

		# Create internal tokens
		token_data = {
			"sub": user_id,
			"email": email,
			"name": name,
		}

		access_token = self.jwt_handler.create_access_token(token_data, self.access_token_expires)
		refresh_token = self.jwt_handler.create_refresh_token(
			token_data, self.refresh_token_expires
		)

		# Save refresh token (hashed)
		hashed_refresh = self.jwt_handler.hash_token(refresh_token)
		auth_token = AuthToken(
			id=None,
			user_id=user_id,
			token=hashed_refresh,
			expires_at=datetime.utcnow() + self.refresh_token_expires,
		)
		await self.token_repository.save_token(auth_token)

		# Cache tokens if Redis is available
		if self.session_cache:
			hashed_access = self.jwt_handler.hash_token(access_token)
			await self.session_cache.set_access_token(
				hashed_access, token_data, self.access_token_expires
			)
			await self.session_cache.set_refresh_token(
				hashed_refresh, user_id, self.refresh_token_expires
			)

			session_data = {
				"user_id": user_id,
				"email": email,
				"name": name,
				"auth_provider": "openid",
				"last_login": datetime.now().isoformat(),
			}
			await self.session_cache.set_user_session(
				user_id, session_data, self.refresh_token_expires
			)

		# Update last login
		await self.user_info_repository.update_last_login(user_id, datetime.now())

		return access_token, refresh_token, user_id, user_info

	async def authenticate(self, email: str, password: str) -> tuple[str, str, str] | None:
		"""
		Not applicable for OpenID Connect.
		Use authenticate_with_code instead.

		Args:
			email: Not used
			password: Not used

		Returns:
			None (not supported)
		"""
		raise NotImplementedError(
			"Direct email/password authentication not supported for OpenID Connect. "
			"Use authenticate_with_code() with authorization code instead."
		)

	async def refresh_token(self, refresh_token: str) -> str | None:
		"""
		Refresh an access token using internal refresh token.

		Args:
			refresh_token: Internal refresh token

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

		hashed_refresh = self.jwt_handler.hash_token(refresh_token)

		# Try cache first if available
		if self.session_cache:
			user_id = await self.session_cache.get_refresh_token(hashed_refresh)
			if not user_id:
				token = await self.token_repository.get_token_by_value(hashed_refresh)
				if not token or not token.is_valid():
					return None
				user_id = token.user_id
		else:
			token = await self.token_repository.get_token_by_value(hashed_refresh)
			if not token or not token.is_valid():
				return None

		# Create new access token
		token_data = {
			"sub": payload["sub"],
			"email": payload["email"],
			"name": payload.get("name"),
		}

		access_token = self.jwt_handler.create_access_token(token_data, self.access_token_expires)

		# Cache the new access token if Redis is available
		if self.session_cache:
			hashed_access = self.jwt_handler.hash_token(access_token)
			await self.session_cache.set_access_token(
				hashed_access, token_data, self.access_token_expires
			)

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

			if self.session_cache:
				await self.session_cache.revoke_refresh_token(hashed_refresh)

			return True
		except Exception:
			return False

	async def verify_access_token(self, access_token: str) -> dict | None:
		"""
		Verify and decode an internal access token.

		Args:
			access_token: The access token to verify

		Returns:
			Token payload if valid, None otherwise
		"""
		hashed_access = self.jwt_handler.hash_token(access_token)

		# Try cache first if available
		if self.session_cache:
			cached_data = await self.session_cache.get_access_token(hashed_access)
			if cached_data:
				return cached_data

		# Verify JWT
		is_valid, payload = self.jwt_handler.verify_token(access_token)
		if not is_valid or not payload:
			return None

		if payload.get("type") != "access":
			return None

		# Cache for future requests if Redis is available
		if self.session_cache and payload:
			token_data = {
				"sub": payload["sub"],
				"email": payload.get("email"),
				"name": payload.get("name"),
			}
			await self.session_cache.set_access_token(
				hashed_access, token_data, self.access_token_expires
			)

		return payload
