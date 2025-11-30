"""
Ejemplo de integración de los 3 sistemas con DI manual.

Este enfoque usa:
- Shared database session
- Manual dependency injection
- Clear ownership and lifecycle
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

# Importar los 3 sistemas
# from auth import AuthConfig, VexenAuth
# from rbac import RBACConfig, VexenRBAC
# from vexen_user import VexenUser, VexenUserConfig


class VexenContainer:
	"""
	Container for managing all Vexen systems with shared resources.

	This is a manual DI container that manages:
	- Shared database engine and session
	- Integration between auth, user, and rbac
	- Proper lifecycle management
	"""

	def __init__(self, database_url: str, secret_key: str):
		self.database_url = database_url
		self.secret_key = secret_key

		# Shared resources
		self._engine: AsyncEngine | None = None
		self._session_factory: async_sessionmaker[AsyncSession] | None = None
		self._session: AsyncSession | None = None

		# Systems
		self._user_repo = None
		self._role_repo = None
		self._auth_provider = None

		# Services
		self.user_service = None
		self.rbac_service = None
		self.auth_service = None

	async def init(self):
		"""Initialize all systems with shared resources"""
		# 1. Create shared database engine
		self._engine = create_async_engine(self.database_url, echo=False)

		self._session_factory = async_sessionmaker(
			self._engine, class_=AsyncSession, expire_on_commit=False
		)

		# 2. Create session for this context
		self._session = self._session_factory()

		# 3. Create tables for all systems
		# await self._create_all_tables()

		# 4. Initialize repositories with shared session
		# self._user_repo = UserRepository(self._session)
		# self._role_repo = RoleRepository(self._session)
		# self._permission_repo = PermissionRepository(self._session)
		# self._token_repo = TokenRepository(self._session)
		# self._credential_repo = AuthRepository(self._session)

		# 5. Initialize services with dependencies
		# self.user_service = UserService(repository=self._user_repo)
		# self.rbac_service = RBACService(
		#     role_repository=self._role_repo,
		#     permission_repository=self._permission_repo
		# )

		# 6. Initialize auth with user and rbac dependencies
		# user_info_adapter = UserInfoAdapter(user_repository=self._user_repo)
		# role_info_adapter = RoleInfoAdapter(role_repository=self._role_repo)
		# jwt_handler = JWTHandler(secret_key=self.secret_key)

		# auth_provider = LocalAuthProvider(
		#     auth_repository=self._credential_repo,
		#     token_repository=self._token_repo,
		#     user_info_repository=user_info_adapter,
		#     role_info_repository=role_info_adapter,
		#     jwt_handler=jwt_handler
		# )

		# self.auth_service = AuthService(auth_provider=auth_provider)

	async def commit(self):
		"""Commit transaction for all systems"""
		if self._session:
			await self._session.commit()

	async def rollback(self):
		"""Rollback transaction for all systems"""
		if self._session:
			await self._session.rollback()

	async def close(self):
		"""Close all resources"""
		if self._session:
			await self._session.close()
		if self._engine:
			await self._engine.dispose()

	async def __aenter__(self):
		await self.init()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		if exc_type:
			await self.rollback()
		await self.close()


async def main():
	"""Example usage with manual DI container"""
	async with VexenContainer(
		database_url="postgresql+asyncpg://user:pass@localhost/db",
		secret_key="my-secret-key"
	) as container:
		# All services share the same DB session and transaction

		# Create a user
		# user = await container.user_service.create(...)

		# Assign a role (from RBAC)
		# role = await container.rbac_service.roles.get("admin")

		# Login (Auth uses User and RBAC internally)
		# login = await container.auth_service.login(...)

		# Everything in one transaction
		await container.commit()


if __name__ == "__main__":
	asyncio.run(main())
