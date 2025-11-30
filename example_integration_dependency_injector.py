"""
Ejemplo de integración con dependency-injector.

Ventajas:
- Configuración declarativa
- Lazy loading automático
- Singleton/Factory patterns built-in
- Fácil testing (override dependencies)

Desventajas:
- Más complejo
- "Magic" dificulta debugging
- Dependencia extra
"""

import asyncio

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


class DatabaseContainer(containers.DeclarativeContainer):
	"""Container for database resources"""

	# Configuration
	config = providers.Configuration()

	# Database engine (singleton)
	engine = providers.Singleton(
		create_async_engine,
		config.database_url,
		echo=config.echo,
	)

	# Session factory
	session_factory = providers.Singleton(
		async_sessionmaker,
		engine,
		class_=AsyncSession,
		expire_on_commit=False,
	)

	# Session (scoped - one per request/context)
	session = providers.Factory(
		lambda factory: factory(),
		factory=session_factory,
	)


class RepositoryContainer(containers.DeclarativeContainer):
	"""Container for repositories"""

	# Database container
	db = providers.DependenciesContainer()

	# Repositories
	user_repository = providers.Factory(
		# UserRepository,
		lambda session: None,  # Placeholder
		session=db.session,
	)

	role_repository = providers.Factory(
		# RoleRepository,
		lambda session: None,  # Placeholder
		session=db.session,
	)

	permission_repository = providers.Factory(
		# PermissionRepository,
		lambda session: None,  # Placeholder
		session=db.session,
	)

	token_repository = providers.Factory(
		# TokenRepository,
		lambda session: None,  # Placeholder
		session=db.session,
	)

	credential_repository = providers.Factory(
		# AuthRepository,
		lambda session: None,  # Placeholder
		session=db.session,
	)


class AdapterContainer(containers.DeclarativeContainer):
	"""Container for adapters"""

	# Dependencies
	repositories = providers.DependenciesContainer()

	# Adapters
	user_info_adapter = providers.Factory(
		# UserInfoAdapter,
		lambda repo: None,  # Placeholder
		user_repository=repositories.user_repository,
	)

	role_info_adapter = providers.Factory(
		# RoleInfoAdapter,
		lambda repo: None,  # Placeholder
		role_repository=repositories.role_repository,
	)


class SecurityContainer(containers.DeclarativeContainer):
	"""Container for security components"""

	config = providers.Configuration()

	jwt_handler = providers.Singleton(
		# JWTHandler,
		lambda key: None,  # Placeholder
		secret_key=config.secret_key,
		algorithm=config.algorithm,
	)

	password_hasher = providers.Singleton(
		# PasswordHasher,
		lambda: None,  # Placeholder
	)


class ProviderContainer(containers.DeclarativeContainer):
	"""Container for authentication providers"""

	# Dependencies
	repositories = providers.DependenciesContainer()
	adapters = providers.DependenciesContainer()
	security = providers.DependenciesContainer()

	# Auth provider
	local_auth_provider = providers.Factory(
		# LocalAuthProvider,
		lambda *args: None,  # Placeholder
		auth_repository=repositories.credential_repository,
		token_repository=repositories.token_repository,
		user_info_repository=adapters.user_info_adapter,
		jwt_handler=security.jwt_handler,
	)


class ServiceContainer(containers.DeclarativeContainer):
	"""Container for application services"""

	# Dependencies
	repositories = providers.DependenciesContainer()
	providers_container = providers.DependenciesContainer()

	# User service
	user_service = providers.Factory(
		# UserService,
		lambda repo: None,  # Placeholder
		repository=repositories.user_repository,
	)

	# RBAC service
	rbac_service = providers.Factory(
		# RBACService,
		lambda *args: None,  # Placeholder
		role_repository=repositories.role_repository,
		permission_repository=repositories.permission_repository,
	)

	# Auth service
	auth_service = providers.Factory(
		# AuthService,
		lambda provider: None,  # Placeholder
		auth_provider=providers_container.local_auth_provider,
	)


class VexenContainer(containers.DeclarativeContainer):
	"""Main container that wires everything together"""

	# Configuration
	config = providers.Configuration()

	# Sub-containers
	db = providers.Container(
		DatabaseContainer,
		config=config.database,
	)

	repositories = providers.Container(
		RepositoryContainer,
		db=db,
	)

	adapters = providers.Container(
		AdapterContainer,
		repositories=repositories,
	)

	security = providers.Container(
		SecurityContainer,
		config=config.security,
	)

	providers_container = providers.Container(
		ProviderContainer,
		repositories=repositories,
		adapters=adapters,
		security=security,
	)

	services = providers.Container(
		ServiceContainer,
		repositories=repositories,
		providers_container=providers_container,
	)


# Usage with dependency injection
@inject
async def create_user_use_case(
	user_service = Provide[VexenContainer.services.user_service],
	auth_service = Provide[VexenContainer.services.auth_service],
):
	"""Example use case with automatic dependency injection"""
	# Dependencies are automatically injected
	# user = await user_service.create(...)
	# auth = await auth_service.login(...)
	pass


async def main():
	"""Example usage with dependency-injector"""
	# Create and configure container
	container = VexenContainer()

	container.config.database.from_dict({
		"database_url": "postgresql+asyncpg://user:pass@localhost/db",
		"echo": False,
	})

	container.config.security.from_dict({
		"secret_key": "my-secret-key",
		"algorithm": "HS256",
	})

	# Wire the container to enable @inject
	container.wire(modules=[__name__])

	# Use services
	user_service = container.services.user_service()
	auth_service = container.services.auth_service()

	# Or use with @inject decorator
	await create_user_use_case()

	# For testing, you can override dependencies
	# with container.user_service.override(MockUserService()):
	#     await create_user_use_case()


if __name__ == "__main__":
	asyncio.run(main())
