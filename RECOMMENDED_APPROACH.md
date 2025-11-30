# Enfoque Recomendado: DI Manual con Container

## Por qué NO usar dependency-injector (por ahora)

1. **Tus proyectos son pequeños y bien estructurados**
   - ~5-10 clases por proyecto
   - Hexagonal architecture ya proporciona desacoplamiento
   - Factories + dataclasses ya funcionan bien

2. **Arquitectura limpia actual**
   - Ports/Adapters ya implementan IoC
   - Type hints completos
   - Fácil de entender y debuggear

3. **YAGNI (You Aren't Gonna Need It)**
   - No tienes 50+ servicios
   - No necesitas lazy loading complejo
   - No tienes múltiples scopes (request/session/app)

## Propuesta: VexenContainer Manual

### Ventajas
✅ **Explícito**: Código claro y directo
✅ **Type-safe**: IDE y mypy funcionan perfectamente
✅ **Sin dependencias**: Cero librerías extra
✅ **Fácil debugging**: Stack traces claros
✅ **Shared resources**: Session compartida entre sistemas
✅ **Testing simple**: Inyección manual de mocks
✅ **Transacciones**: Commit/rollback conjunto

### Estructura Propuesta

```
vexen/
├── vexen-user/           # Paquete independiente
├── vexen-rbac/           # Paquete independiente
├── vexen-auth/           # Paquete independiente
└── vexen-core/           # NUEVO: Paquete integrador
    ├── pyproject.toml    # Depende de user, rbac, auth
    ├── vexen_core/
    │   ├── __init__.py
    │   ├── container.py  # VexenContainer
    │   └── config.py     # VexenConfig
    └── examples/
        └── full_example.py
```

### Implementación del Container

```python
# vexen_core/container.py
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

# Imports de los 3 sistemas
from vexen_user.domain.repository import IUserRepositoryPort
from vexen_user.application.service import UserService
from vexen_user.infraestructure.output.persistence.sqlalchemy.repositories import UserRepository

from vexen_rbac.domain.repository import IRoleRepositoryPort
from vexen_rbac.application.service import RBACService
from vexen_rbac.infraestructure.output.persistence.sqlalchemy.repositories import RoleRepository

from vexen_auth.application.service import AuthService
from vexen_auth.infraestructure.provider import LocalAuthProvider
from vexen_auth.infraestructure.security import JWTHandler


@dataclass
class VexenConfig:
    """Configuración unificada para todos los sistemas"""
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    echo: bool = False


class VexenContainer:
    """
    Container manual para DI de todos los sistemas Vexen.

    Gestiona:
    - Shared database engine y session
    - Repositories para user, rbac, auth
    - Services integrados
    - Lifecycle (init, commit, rollback, close)
    """

    def __init__(self, config: VexenConfig):
        self.config = config

        # Shared database resources
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker | None = None
        self._session: AsyncSession | None = None

        # Repositories (private)
        self._user_repo: IUserRepositoryPort | None = None
        self._role_repo: IRoleRepositoryPort | None = None

        # Services (public)
        self.user: UserService | None = None
        self.rbac: RBACService | None = None
        self.auth: AuthService | None = None

    async def init(self):
        """Initialize all systems with shared resources"""
        # 1. Create shared database
        await self._init_database()

        # 2. Initialize repositories
        self._init_repositories()

        # 3. Initialize services
        self._init_services()

    async def _init_database(self):
        """Create shared database engine and session"""
        self._engine = create_async_engine(
            self.config.database_url,
            echo=self.config.echo
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        self._session = self._session_factory()

        # Create all tables
        # await self._create_tables()

    def _init_repositories(self):
        """Initialize all repositories with shared session"""
        # All repos share the SAME session = SAME transaction
        self._user_repo = UserRepository(self._session)
        self._role_repo = RoleRepository(self._session)
        # ... más repos

    def _init_services(self):
        """Initialize all services with dependency injection"""
        # User service
        self.user = UserService(repository=self._user_repo)

        # RBAC service
        self.rbac = RBACService(role_repository=self._role_repo)

        # Auth service (depends on user and rbac)
        from vexen_auth.infraestructure.output.persistence.sqlalchemy.adapters import (
            UserInfoAdapter
        )

        user_adapter = UserInfoAdapter(user_repository=self._user_repo)
        jwt = JWTHandler(
            secret_key=self.config.secret_key,
            algorithm=self.config.algorithm
        )

        # auth_provider = LocalAuthProvider(
        #     user_info_repository=user_adapter,
        #     jwt_handler=jwt,
        #     ...
        # )

        # self.auth = AuthService(auth_provider=auth_provider)

    async def commit(self):
        """Commit transaction for ALL systems"""
        if self._session:
            await self._session.commit()

    async def rollback(self):
        """Rollback transaction for ALL systems"""
        if self._session:
            await self._session.rollback()

    async def close(self):
        """Close all resources"""
        if self._session:
            await self._session.close()
        if self._engine:
            await self._engine.dispose()

    async def __aenter__(self):
        """Context manager entry"""
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            # Rollback on exception
            await self.rollback()
        await self.close()
```

### Uso del Container

```python
# examples/full_example.py
import asyncio
from vexen_core.container import VexenContainer, VexenConfig


async def main():
    """Ejemplo completo de integración"""

    config = VexenConfig(
        database_url="postgresql+asyncpg://user:pass@localhost/vexen",
        secret_key="your-secret-key"
    )

    # Opción 1: Context manager (recomendado)
    async with VexenContainer(config) as vexen:
        # Todos los servicios comparten la misma transacción

        # 1. Crear usuario
        user_request = CreateUserRequest(
            email="john@example.com",
            name="John Doe",
            password="secret123"
        )
        user_response = await vexen.user.create(user_request)

        if not user_response.success:
            print(f"Error: {user_response.error}")
            return

        # 2. Asignar rol (TODO: cuando tengas el método)
        # role = await vexen.rbac.roles.get("admin")
        # await vexen.rbac.roles.assign_to_user(user_response.data.id, role.id)

        # 3. Login
        login_request = LoginRequest(
            email="john@example.com",
            password="secret123"
        )
        login_response = await vexen.auth.login(login_request)

        if login_response:
            print(f"Access token: {login_response.access_token}")

        # 4. Commit todo junto (automático en __aexit__)
        await vexen.commit()

    # Opción 2: Manual
    vexen = VexenContainer(config)
    await vexen.init()

    try:
        # ... operaciones
        await vexen.commit()
    except Exception as e:
        await vexen.rollback()
        raise
    finally:
        await vexen.close()


if __name__ == "__main__":
    asyncio.run(main())
```

### Testing con el Container

```python
# tests/test_integration.py
import pytest
from unittest.mock import AsyncMock
from vexen_core.container import VexenContainer, VexenConfig


@pytest.fixture
async def container():
    """Container de prueba con mocks"""
    config = VexenConfig(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-key"
    )

    container = VexenContainer(config)
    await container.init()

    yield container

    await container.close()


async def test_user_creation(container):
    """Test creación de usuario"""
    request = CreateUserRequest(
        email="test@example.com",
        name="Test User",
        password="password"
    )

    response = await container.user.create(request)

    assert response.success
    assert response.data.email == "test@example.com"


async def test_full_flow_with_transaction(container):
    """Test flujo completo con transacción"""
    # Create user
    user = await container.user.create(...)

    # Login
    login = await container.auth.login(...)

    # Todo en la misma transacción
    await container.commit()


async def test_rollback_on_error(container):
    """Test rollback cuando hay error"""
    try:
        # Operaciones
        await container.user.create(...)

        # Simular error
        raise Exception("Something went wrong")

    except Exception:
        # Rollback automático
        await container.rollback()

    # Verificar que no se guardó nada
    users = await container.user.list()
    assert users.pagination.total_items == 0
```

## Cuándo Migrar a dependency-injector

Considera migrar SOLO SI:

1. **Escala**: Tienes >20 servicios diferentes
2. **Complejidad**: Necesitas múltiples scopes (singleton, request, transient)
3. **Lazy loading**: Performance crítica con muchas dependencias
4. **Configuración**: Necesitas cargar config desde múltiples fuentes
5. **Equipo**: El equipo está familiarizado con DI containers

## Conclusión

Para tus 3 proyectos actuales:

🎯 **Implementa VexenContainer manual**
- Más simple
- Más explícito
- Type-safe completo
- Fácil testing
- Sin dependencias extra

⏸️ **Pospón dependency-injector**
- Lo considerarás cuando realmente lo necesites
- Por ahora es YAGNI (You Aren't Gonna Need It)

💡 **Siguiente paso**:
1. Crea el paquete `vexen-core`
2. Implementa `VexenContainer` como se muestra arriba
3. Usa el container en tus aplicaciones
4. Mantén cada proyecto (user, rbac, auth) independiente
