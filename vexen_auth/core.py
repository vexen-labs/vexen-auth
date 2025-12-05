"""VexenAuth public API."""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from vexen_auth.application.service.auth_service import AuthService
from vexen_auth.domain.repository.session_cache_port import ISessionCachePort
from vexen_auth.domain.repository.user_info_port import IUserInfoPort
from vexen_auth.infraestructure.output.persistence.sqlalchemy.adapters import (
	auth_repository_adapter,
)
from vexen_auth.infraestructure.output.persistence.sqlalchemy.adapters.user_info_adapter import (
	UserInfoAdapter,
)
from vexen_auth.infraestructure.output.persistence.sqlalchemy.models import Base
from vexen_auth.infraestructure.output.persistence.sqlalchemy.repositories.auth_repository import (
	AuthRepository,
)
from vexen_auth.infraestructure.output.persistence.sqlalchemy.repositories.token_repository import (
	TokenRepository,
)
from vexen_auth.infraestructure.provider.local_auth_provider import LocalAuthProvider
from vexen_auth.infraestructure.security.jwt_handler import JWTHandler


@dataclass
class AuthConfig:
	"""Configuration for VexenAuth"""

	# Database configuration
	database_url: str
	adapter: str = "sqlalchemy"

	# JWT configuration
	secret_key: str = "change-me-in-production"
	algorithm: str = "HS256"
	access_token_expires_minutes: int = 15
	refresh_token_expires_days: int = 30

	# Redis configuration (optional, for session caching)
	redis_url: str | None = None
	enable_redis_cache: bool = False

	# External service integration (optional)
	user_service: object | None = None

	# Direct repository access (optional, alternative to services)
	user_repository: object | None = None

	# OpenID Connect configuration (optional)
	openid_providers: dict[str, dict] | None = None  # Dict of provider_name -> config


class VexenAuth:
	"""
	VexenAuth - Authentication system for Vexen.

	Provides authentication operations including login, token refresh,
	logout, and user verification.

	Example:
		>>> from vexen_auth.core import VexenAuth, AuthConfig
		>>>
		>>> config = AuthConfig(
		...     database_url="postgresql+asyncpg://user:pass@localhost/db",
		...     secret_key="your-secret-key"
		... )
		>>>
		>>> auth = VexenAuth(config)
		>>> async with auth:
		...     from vexen_auth.application.dto import LoginRequest
		...     request = LoginRequest(email="user@example.com", password="password")
		...     response = await auth.service.login(request)
		...     if response:
		...         print(f"Access token: {response.access_token}")
	"""

	def __init__(self, config: AuthConfig):
		"""
		Initialize VexenAuth.

		Args:
			config: Authentication configuration
		"""
		self.config = config
		self._engine: AsyncEngine | None = None
		self._session: AsyncSession | None = None
		self._session_cache: ISessionCachePort | None = None
		self._service: AuthService | None = None
		self._openid_service = None

	async def init(self) -> None:
		"""Initialize the auth system"""
		if self.config.adapter == "sqlalchemy":
			await self._init_sqlalchemy()

	async def _init_sqlalchemy(self) -> None:
		"""Initialize SQLAlchemy adapter"""
		# Create engine
		self._engine = create_async_engine(self.config.database_url, echo=False)

		# Create session
		from sqlalchemy.orm import sessionmaker

		async_session = sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)
		self._session = async_session()

		# Create tables
		async with self._engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)

		# Initialize Redis cache if enabled
		if self.config.enable_redis_cache:
			from vexen_auth.infraestructure.output.cache.redis import RedisSessionCache

			redis_url = self.config.redis_url or "redis://localhost:6379/0"
			self._session_cache = RedisSessionCache(redis_url=redis_url)

		# Initialize repositories
		auth_repo = AuthRepository(self._session)
		token_repo = TokenRepository(self._session)

		# Initialize adapters
		user_info_adapter: IUserInfoPort = UserInfoAdapter(
			user_service=self.config.user_service,
			user_repository=self.config.user_repository,
		)

		auth_repo_adapter = auth_repository_adapter.AuthRepositoryAdapter(
			auth_repo, user_info_adapter
		)

		# Initialize JWT handler
		jwt_handler = JWTHandler(secret_key=self.config.secret_key, algorithm=self.config.algorithm)

		# Initialize auth provider with optional Redis cache
		auth_provider = LocalAuthProvider(
			auth_repository=auth_repo_adapter,
			token_repository=token_repo,
			user_info_repository=user_info_adapter,
			jwt_handler=jwt_handler,
			access_token_expires=timedelta(minutes=self.config.access_token_expires_minutes),
			refresh_token_expires=timedelta(days=self.config.refresh_token_expires_days),
			session_cache=self._session_cache,
		)

		# Initialize service
		self._service = AuthService(auth_provider=auth_provider)

		# Initialize OpenID providers if configured
		if self.config.openid_providers:
			from vexen_auth.application.dto.openid_dto import OpenIDProviderConfig
			from vexen_auth.application.service.openid_service import OpenIDService
			from vexen_auth.infraestructure.provider.openid_provider import OpenIDProvider

			openid_providers = {}
			for provider_name, provider_config_dict in self.config.openid_providers.items():
				# Create OpenIDProvider instance
				provider_config = OpenIDProviderConfig(**provider_config_dict)

				if provider_config.enabled:
					openid_provider = OpenIDProvider(
						client_id=provider_config.client_id,
						client_secret=provider_config.client_secret,
						discovery_url=provider_config.discovery_url,
						redirect_uri=provider_config.redirect_uri,
						token_repository=token_repo,
						user_info_repository=user_info_adapter,
						jwt_handler=jwt_handler,
						auth_repository=auth_repo_adapter,
						access_token_expires=timedelta(
							minutes=self.config.access_token_expires_minutes
						),
						refresh_token_expires=timedelta(days=self.config.refresh_token_expires_days),
						session_cache=self._session_cache,
						scopes=provider_config.scopes,
					)
					openid_providers[provider_name] = openid_provider

			if openid_providers:
				self._openid_service = OpenIDService(providers=openid_providers)

	async def close(self) -> None:
		"""Close all connections"""
		if self._session:
			await self._session.close()
		if self._session_cache:
			await self._session_cache.close()
		if self._engine:
			await self._engine.dispose()

	async def __aenter__(self):
		"""Async context manager entry"""
		await self.init()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		"""Async context manager exit"""
		await self.close()

	@property
	def service(self) -> AuthService:
		"""
		Get the auth service.

		Returns:
			AuthService instance

		Raises:
			RuntimeError: If VexenAuth is not initialized
		"""
		if self._service is None:
			raise RuntimeError(
				"VexenAuth not initialized. Call init() or use async context manager."
			)
		return self._service

	@property
	def openid(self):
		"""
		Get the OpenID service.

		Returns:
			OpenIDService instance or None if not configured

		Raises:
			RuntimeError: If VexenAuth is not initialized
			ValueError: If OpenID providers are not configured
		"""
		if self._service is None:
			raise RuntimeError(
				"VexenAuth not initialized. Call init() or use async context manager."
			)

		if self._openid_service is None:
			raise ValueError(
				"OpenID Connect not configured. Add openid_providers to AuthConfig."
			)

		return self._openid_service

	async def commit(self) -> None:
		"""Commit the current transaction"""
		if self._session:
			await self._session.commit()

	async def rollback(self) -> None:
		"""Rollback the current transaction"""
		if self._session:
			await self._session.rollback()
