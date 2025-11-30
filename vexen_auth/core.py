"""VexenAuth public API."""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from vexen_auth.application.service.auth_service import AuthService
from vexen_auth.domain.repository.user_info_port import IUserInfoPort
from vexen_auth.infraestructure.output.persistence.sqlalchemy.adapters.auth_repository_adapter import (
	AuthRepositoryAdapter,
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

	# External service integration (optional)
	user_service = None

	# Direct repository access (optional, alternative to services)
	user_repository = None


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
		self._service: AuthService | None = None

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

		# Initialize repositories
		auth_repo = AuthRepository(self._session)
		token_repo = TokenRepository(self._session)

		# Initialize adapters
		user_info_adapter: IUserInfoPort = UserInfoAdapter(
			user_service=self.config.user_service,
			user_repository=self.config.user_repository,
		)

		auth_repo_adapter = AuthRepositoryAdapter(auth_repo, user_info_adapter)

		# Initialize JWT handler
		jwt_handler = JWTHandler(secret_key=self.config.secret_key, algorithm=self.config.algorithm)

		# Initialize auth provider
		auth_provider = LocalAuthProvider(
			auth_repository=auth_repo_adapter,
			token_repository=token_repo,
			user_info_repository=user_info_adapter,
			jwt_handler=jwt_handler,
			access_token_expires=timedelta(minutes=self.config.access_token_expires_minutes),
			refresh_token_expires=timedelta(days=self.config.refresh_token_expires_days),
		)

		# Initialize service
		self._service = AuthService(auth_provider=auth_provider)

	async def close(self) -> None:
		"""Close all connections"""
		if self._session:
			await self._session.close()
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

	async def commit(self) -> None:
		"""Commit the current transaction"""
		if self._session:
			await self._session.commit()

	async def rollback(self) -> None:
		"""Rollback the current transaction"""
		if self._session:
			await self._session.rollback()
