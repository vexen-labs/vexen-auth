"""DTOs for authentication operations."""

from dataclasses import dataclass


@dataclass
class LoginRequest:
	"""Request to login"""

	email: str
	password: str


@dataclass
class LoginResponse:
	"""Response from successful login"""

	access_token: str
	refresh_token: str
	user_id: str


@dataclass
class RefreshTokenRequest:
	"""Request to refresh access token"""

	refresh_token: str


@dataclass
class RefreshTokenResponse:
	"""Response from refresh token"""

	access_token: str


@dataclass
class LogoutRequest:
	"""Request to logout"""

	refresh_token: str


@dataclass
class VerifyTokenRequest:
	"""Request to verify access token"""

	access_token: str


@dataclass
class VerifyTokenResponse:
	"""Response from token verification"""

	valid: bool
	user_id: str | None = None
