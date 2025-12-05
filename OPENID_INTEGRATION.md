# OpenID Connect Integration

VexenAuth incluye soporte completo para OpenID Connect (OIDC), permitiendo autenticación con múltiples proveedores como Google, Microsoft Azure AD, Keycloak, Auth0, Okta, y cualquier proveedor compatible con OpenID Connect.

## Características

- ✅ **Múltiples Proveedores**: Soporte para Google, Azure AD, Keycloak, Auth0, Okta, etc.
- ✅ **Auto-descubrimiento**: Configuración automática mediante OpenID Discovery
- ✅ **Gestión de Tokens**: Tokens de acceso y refresh internos después de autenticación
- ✅ **Verificación de ID Token**: Validación completa de JWT con JWKS
- ✅ **Caché Redis**: Soporte opcional para mejorar rendimiento
- ✅ **Type-Safe**: Totalmente tipado con dataclasses
- ✅ **Integración Fácil**: Compatible con FastAPI, Flask, Django, etc.

## Instalación

```bash
pip install vexen-auth
```

Las dependencias necesarias (`authlib`, `httpx`) se instalan automáticamente.

## Configuración Rápida

### 1. Configurar Proveedor OpenID

```python
from vexen_auth import VexenAuth
from vexen_auth.core import AuthConfig

config = AuthConfig(
    database_url="postgresql+asyncpg://user:pass@localhost/db",
    secret_key="your-secret-key",
    openid_providers={
        "google": {
            "name": "google",
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "client_secret": "YOUR_CLIENT_SECRET",
            "discovery_url": "https://accounts.google.com/.well-known/openid-configuration",
            "redirect_uri": "http://localhost:8000/auth/callback/google",
            "scopes": ["openid", "email", "profile"],
            "enabled": True
        }
    }
)

auth = VexenAuth(config)
await auth.init()
```

### 2. Flujo de Autenticación

```python
from vexen_auth.application.dto import (
    OpenIDAuthRequest,
    OpenIDCallbackRequest
)

# Paso 1: Obtener URL de autorización
auth_request = OpenIDAuthRequest(
    provider="google",
    state="random-csrf-token"
)

auth_response = await auth.openid.initiate_auth(auth_request)
# Redirigir usuario a: auth_response.authorization_url

# Paso 2: Manejar callback OAuth
callback_request = OpenIDCallbackRequest(
    code="authorization_code_from_provider",
    state="random-csrf-token",
    provider="google"
)

login_response = await auth.openid.handle_callback(callback_request)

if login_response:
    access_token = login_response.access_token
    refresh_token = login_response.refresh_token
    user_id = login_response.user_id
    # Guardar tokens en sesión/cookies
```

## Configuración de Proveedores

### Google OAuth

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto o seleccionar existente
3. Habilitar Google+ API
4. Crear credenciales OAuth 2.0
5. Agregar redirect URI autorizado

```python
{
    "google": {
        "name": "google",
        "client_id": "123456789.apps.googleusercontent.com",
        "client_secret": "GOCSPX-abc123...",
        "discovery_url": "https://accounts.google.com/.well-known/openid-configuration",
        "redirect_uri": "https://yourdomain.com/auth/callback/google",
        "scopes": ["openid", "email", "profile"],
        "enabled": True
    }
}
```

### Microsoft Azure AD / Entra ID

1. Ir a [Azure Portal](https://portal.azure.com/)
2. Azure Active Directory > App registrations
3. Registrar nueva aplicación
4. Configurar redirect URI
5. Generar client secret

```python
{
    "azure": {
        "name": "azure",
        "client_id": "12345678-1234-1234-1234-123456789012",
        "client_secret": "abc123~...",
        "discovery_url": "https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration",
        "redirect_uri": "https://yourdomain.com/auth/callback/azure",
        "scopes": ["openid", "email", "profile"],
        "enabled": True
    }
}
```

### Keycloak

1. Acceder a consola de administración de Keycloak
2. Crear o seleccionar realm
3. Crear nuevo cliente
4. Configurar redirect URIs
5. Habilitar Client authentication
6. Copiar client ID y secret

```python
{
    "keycloak": {
        "name": "keycloak",
        "client_id": "my-app",
        "client_secret": "abc123...",
        "discovery_url": "https://keycloak.example.com/realms/myrealm/.well-known/openid-configuration",
        "redirect_uri": "https://yourdomain.com/auth/callback/keycloak",
        "scopes": ["openid", "email", "profile"],
        "enabled": True
    }
}
```

### Auth0

```python
{
    "auth0": {
        "name": "auth0",
        "client_id": "abc123...",
        "client_secret": "xyz789...",
        "discovery_url": "https://yourtenant.auth0.com/.well-known/openid-configuration",
        "redirect_uri": "https://yourdomain.com/auth/callback/auth0",
        "scopes": ["openid", "email", "profile"],
        "enabled": True
    }
}
```

### Okta

```python
{
    "okta": {
        "name": "okta",
        "client_id": "abc123...",
        "client_secret": "xyz789...",
        "discovery_url": "https://yourdomain.okta.com/.well-known/openid-configuration",
        "redirect_uri": "https://yourdomain.com/auth/callback/okta",
        "scopes": ["openid", "email", "profile"],
        "enabled": True
    }
}
```

## Integración con FastAPI

```python
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from vexen_auth import VexenAuth
from vexen_auth.application.dto import OpenIDAuthRequest, OpenIDCallbackRequest

app = FastAPI()

# Inicializar VexenAuth
auth = VexenAuth(config)

@app.on_event("startup")
async def startup():
    await auth.init()

@app.on_event("shutdown")
async def shutdown():
    await auth.close()

# Rutas de autenticación
@app.get("/auth/login/{provider}")
async def login(provider: str):
    """Iniciar login con proveedor OpenID"""
    auth_request = OpenIDAuthRequest(provider=provider)
    auth_response = await auth.openid.initiate_auth(auth_request)

    if not auth_response:
        raise HTTPException(status_code=400, detail="Invalid provider")

    # En producción, guardar state en sesión para CSRF
    return RedirectResponse(url=auth_response.authorization_url)

@app.get("/auth/callback/{provider}")
async def callback(provider: str, code: str, state: str = None):
    """Manejar callback de OAuth"""
    callback_request = OpenIDCallbackRequest(
        code=code,
        state=state,
        provider=provider
    )

    login_response = await auth.openid.handle_callback(callback_request)

    if not login_response:
        raise HTTPException(status_code=401, detail="Authentication failed")

    # Guardar tokens en cookies HTTP-only
    response = RedirectResponse(url="/dashboard")
    response.set_cookie(
        key="access_token",
        value=login_response.access_token,
        httponly=True,
        secure=True,  # Solo HTTPS en producción
        samesite="lax"
    )
    response.set_cookie(
        key="refresh_token",
        value=login_response.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax"
    )

    return response

# Dependency para rutas protegidas
async def get_current_user(request: Request):
    """Verificar token de acceso"""
    access_token = request.cookies.get("access_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Intentar con todos los proveedores habilitados
    for provider_name in ["google", "azure", "keycloak"]:
        try:
            token_payload = await auth.openid.verify_token(provider_name, access_token)
            if token_payload:
                return token_payload
        except:
            continue

    raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/api/me")
async def get_me(current_user = Depends(get_current_user)):
    """Ruta protegida - obtener información del usuario"""
    return {
        "user_id": current_user["sub"],
        "email": current_user["email"],
        "name": current_user.get("name")
    }

@app.post("/auth/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        # Intentar revocar con todos los proveedores
        for provider_name in ["google", "azure", "keycloak"]:
            try:
                await auth.openid.logout(provider_name, refresh_token)
            except:
                pass

    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response
```

## API Reference

### OpenID Service

#### `initiate_auth(request: OpenIDAuthRequest) -> OpenIDAuthResponse | None`

Inicia el flujo de autenticación OpenID Connect.

```python
auth_request = OpenIDAuthRequest(
    provider="google",
    state="csrf-token"
)
response = await auth.openid.initiate_auth(auth_request)
```

#### `handle_callback(request: OpenIDCallbackRequest) -> OpenIDLoginResponse | None`

Maneja el callback de OAuth y completa la autenticación.

```python
callback_request = OpenIDCallbackRequest(
    code="auth_code",
    state="csrf-token",
    provider="google"
)
response = await auth.openid.handle_callback(callback_request)
```

#### `refresh_token(provider_name: str, refresh_token: str) -> str | None`

Refresca un token de acceso.

```python
new_token = await auth.openid.refresh_token("google", refresh_token)
```

#### `logout(provider_name: str, refresh_token: str) -> bool`

Revoca un refresh token.

```python
success = await auth.openid.logout("google", refresh_token)
```

#### `verify_token(provider_name: str, access_token: str) -> dict | None`

Verifica un token de acceso.

```python
payload = await auth.openid.verify_token("google", access_token)
```

## Mejores Prácticas de Seguridad

1. **HTTPS en Producción**: Siempre usa HTTPS para redirect URIs
2. **HTTP-only Cookies**: Almacena tokens en cookies HTTP-only
3. **CSRF Protection**: Usa el parámetro `state` para validación CSRF
4. **Secrets Seguros**: Guarda client secrets en variables de entorno
5. **Tokens de Corta Duración**: Usa access tokens de 15-30 minutos
6. **Rotación de Tokens**: Rota refresh tokens regularmente
7. **Rate Limiting**: Implementa rate limiting en endpoints de auth
8. **Validación de State**: Verifica el parámetro state en callbacks

## Caché con Redis (Opcional)

Para mejorar el rendimiento, habilita caché Redis:

```python
config = AuthConfig(
    database_url="postgresql+asyncpg://user:pass@localhost/db",
    secret_key="your-secret-key",
    enable_redis_cache=True,
    redis_url="redis://localhost:6379/0",
    openid_providers={...}
)
```

## Troubleshooting

### Error: "Invalid redirect URI"

- Verifica que el redirect_uri en la configuración coincida exactamente con el configurado en el proveedor
- Asegúrate de incluir el protocolo (http:// o https://)

### Error: "Invalid state parameter"

- Implementa validación de state correctamente
- Guarda el state en sesión antes de redirigir al usuario

### Error: "User not found"

- El usuario no existe en tu base de datos
- Implementa creación automática de usuarios o registro previo

## Ejemplos Completos

Ver [example_openid_usage.py](./example_openid_usage.py) para ejemplos completos y casos de uso.

## Soporte

- Issues: [GitHub Issues](https://github.com/vexen-labs/vexen-auth/issues)
- Documentación: [README.md](./README.md)

## Licencia

MIT
