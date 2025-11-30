# Comparación: DI Manual vs dependency-injector

## Estado Actual (DI Manual con Dataclasses)

### ✅ Ventajas
- **Explícito**: Puedes seguir el código línea por línea
- **Type-safe**: Type hints funcionan perfectamente
- **Simple**: No requiere aprender nueva librería
- **Debugging fácil**: Stack traces claros
- **IDE support**: Autocompletado funciona bien
- **Ya implementado**: Factories + dataclasses funcionan

### ❌ Desventajas
- **Boilerplate**: Código repetitivo para crear dependencias
- **Acoplamiento temporal**: El orden de inicialización importa
- **Difícil compartir recursos**: Complicado compartir session entre sistemas
- **Testing**: Más manual para inyectar mocks
- **Configuración**: No hay un lugar centralizado

### Código Ejemplo
```python
# Simple pero manual
async def init(self):
    self._engine = create_async_engine(...)
    self._session = sessionmaker(...)()
    self._repo = UserRepository(self._session)
    self._service = UserService(repository=self._repo)
```

---

## Con dependency-injector

### ✅ Ventajas
- **Declarativo**: Configuración centralizada
- **Lazy loading**: Solo crea lo que necesitas
- **Scopes**: Singleton, Factory, Scoped (por request)
- **Testing**: Override fácil de dependencias
- **Wiring**: `@inject` automático
- **Configuración externa**: YAML, ENV, dict
- **Menos boilerplate**: Una vez configurado

### ❌ Desventajas
- **Complejidad**: Curva de aprendizaje
- **Magic**: Menos explícito, más difícil debuggear
- **Dependencia externa**: +1 librería
- **Type hints limitados**: Provide[] no es totalmente type-safe
- **Overhead**: Pequeño overhead de performance
- **Overkill**: Para proyectos pequeños

### Código Ejemplo
```python
# Más magic pero menos boilerplate
class Container(containers.DeclarativeContainer):
    db = providers.Singleton(create_async_engine, config.url)
    repo = providers.Factory(UserRepository, session=db)
    service = providers.Factory(UserService, repository=repo)

# Uso
@inject
def my_function(service: UserService = Provide[Container.service]):
    ...
```

---

## Mi Recomendación: Enfoque Híbrido

### Fase 1: Mejora tu DI Manual (AHORA) ⭐
```python
# Crea un Container manual simple
class VexenContainer:
    """Simple DI container sin dependencias externas"""

    def __init__(self, database_url: str, secret_key: str):
        self.database_url = database_url
        self.secret_key = secret_key

        # Shared resources
        self._engine = None
        self._session = None

    async def init(self):
        # Initialize shared resources
        self._engine = create_async_engine(self.database_url)
        self._session_factory = async_sessionmaker(self._engine)
        self._session = self._session_factory()

        # Initialize all repositories with shared session
        self._init_repositories()
        self._init_services()

    def _init_repositories(self):
        # All repos share the same session
        self.user_repo = UserRepository(self._session)
        self.role_repo = RoleRepository(self._session)
        self.auth_repo = AuthRepository(self._session)
        self.token_repo = TokenRepository(self._session)

    def _init_services(self):
        # Services depend on repositories
        self.user_service = UserService(repository=self.user_repo)
        self.rbac_service = RBACService(
            role_repository=self.role_repo
        )

        # Auth depends on user and rbac
        user_adapter = UserInfoAdapter(user_repository=self.user_repo)
        jwt = JWTHandler(secret_key=self.secret_key)

        auth_provider = LocalAuthProvider(
            auth_repository=self.auth_repo,
            token_repository=self.token_repo,
            user_info_repository=user_adapter,
            jwt_handler=jwt
        )

        self.auth_service = AuthService(auth_provider=auth_provider)
```

**Ventajas de este enfoque:**
- ✅ Explícito y fácil de entender
- ✅ Shared session entre todos los sistemas
- ✅ Type-safe completo
- ✅ Sin dependencias externas
- ✅ Fácil de testear (inyectas mocks en __init__)

### Fase 2: Considera dependency-injector SI... (FUTURO)

Solo migra a `dependency-injector` cuando:
- [ ] Tienes >10 servicios diferentes
- [ ] Necesitas múltiples scopes (request, session, application)
- [ ] Quieres configuración externa (YAML/ENV)
- [ ] El equipo está cómodo con DI containers
- [ ] Necesitas lazy loading optimizado
- [ ] Tienes muchos tests con diferentes configuraciones

---

## Caso de Uso Real: Integración de los 3 Sistemas

### Problema Actual
```python
# ❌ Cada sistema tiene su propia sesión
user = VexenUser(config)
rbac = VexenRBAC(config)
auth = VexenAuth(config)

# No pueden compartir transacción
# No pueden hacer rollback conjunto
```

### Solución con Container Manual
```python
# ✅ Todos comparten sesión
container = VexenContainer(database_url="...", secret_key="...")
await container.init()

# Una transacción para todos
try:
    user = await container.user_service.create(...)
    role = await container.rbac_service.roles.assign(user.id, "admin")
    login = await container.auth_service.login(...)

    await container.commit()  # Commit todo junto
except Exception:
    await container.rollback()  # Rollback todo junto
finally:
    await container.close()
```

---

## Conclusión

### Para tus 3 proyectos actuales:

1. **AHORA**: Implementa un `VexenContainer` manual
   - Más simple
   - Más explícito
   - Suficiente para el tamaño actual
   - Fácil de testear

2. **FUTURO**: Considera `dependency-injector` cuando:
   - Los sistemas crezcan significativamente
   - Necesites features avanzadas (scopes, lazy loading)
   - El equipo esté cómodo con el concepto

### Arquitectura Recomendada

```
vexen/
├── vexen_user/       # Proyecto independiente
├── vexen_rbac/       # Proyecto independiente
├── vexen_auth/       # Proyecto independiente
└── vexen_core/       # Proyecto integrador (NUEVO)
    ├── container.py  # VexenContainer (DI manual)
    └── main.py       # Punto de entrada integrado
```

El `vexen_core` sería el que integra los 3 sistemas con shared resources.

---

## Ejemplo de Testing

### Con DI Manual (Actual)
```python
# Fácil inyectar mocks
async def test_user_creation():
    mock_repo = MockUserRepository()
    service = UserService(repository=mock_repo)

    result = await service.create(...)
    assert result.success
```

### Con dependency-injector
```python
# Override en el container
async def test_user_creation():
    container = VexenContainer()

    with container.repositories.user_repository.override(MockUserRepository()):
        service = container.services.user_service()
        result = await service.create(...)
        assert result.success
```

Ambos funcionan, pero el manual es más explícito.
