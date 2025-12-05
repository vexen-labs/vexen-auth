"""DTOs for OpenID Connect operations."""

from dataclasses import dataclass


@dataclass
class OpenIDAuthRequest:
	"""Request to initiate OpenID Connect authentication flow"""

	state: str | None = None  # Optional CSRF protection state
	provider: str = "default"  # Provider identifier (e.g., "google", "azure", "keycloak")


@dataclass
class OpenIDAuthResponse:
	"""Response with authorization URL for OpenID Connect flow"""

	authorization_url: str
	state: str
	provider: str


@dataclass
class OpenIDCallbackRequest:
	"""Request from OpenID Connect callback"""

	code: str  # Authorization code
	state: str | None = None  # State for CSRF validation
	provider: str = "default"  # Provider identifier


@dataclass
class OpenIDLoginResponse:
	"""Response after successful OpenID Connect login"""

	access_token: str
	refresh_token: str
	user_id: str
	email: str
	name: str | None
	provider: str
	id_token: str | None = None  # Optional OpenID ID token


@dataclass
class OpenIDProviderConfig:
	"""Configuration for an OpenID Connect provider"""

	name: str  # Provider name (e.g., "google", "azure")
	client_id: str
	client_secret: str
	discovery_url: str  # OpenID Connect discovery URL
	redirect_uri: str
	scopes: list[str] | None = None  # Default: ["openid", "email", "profile"]
	enabled: bool = True


@dataclass
class OpenIDUserInfo:
	"""User information from OpenID Connect provider"""

	sub: str  # Subject (unique user ID from provider)
	email: str
	email_verified: bool | None = None
	name: str | None = None
	given_name: str | None = None
	family_name: str | None = None
	picture: str | None = None
	locale: str | None = None
	issuer: str | None = None  # Token issuer
