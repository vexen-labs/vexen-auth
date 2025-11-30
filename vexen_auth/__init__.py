"""VexenAuth - Authentication system for Vexen."""

from .application.dto import (
	LoginRequest,
	LoginResponse,
	LogoutRequest,
	RefreshTokenRequest,
	RefreshTokenResponse,
	VerifyTokenRequest,
	VerifyTokenResponse,
)
from .core import AuthConfig, VexenAuth

__version__ = "0.1.0"

__all__ = [
	"VexenAuth",
	"AuthConfig",
	"LoginRequest",
	"LoginResponse",
	"RefreshTokenRequest",
	"RefreshTokenResponse",
	"LogoutRequest",
	"VerifyTokenRequest",
	"VerifyTokenResponse",
]
