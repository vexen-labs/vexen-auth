"""Auth service for orchestrating auth operations."""

from dataclasses import dataclass, field

from vexen_auth.application.dto.auth_dto import (
	LoginRequest,
	LoginResponse,
	LogoutRequest,
	RefreshTokenRequest,
	RefreshTokenResponse,
	VerifyTokenRequest,
	VerifyTokenResponse,
)
from vexen_auth.application.usecase.auth import AuthUseCaseFactory
from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort


@dataclass
class AuthService:
	"""Service for authentication operations"""

	auth_provider: IAuthProviderPort
	usecases: AuthUseCaseFactory = field(init=False)

	def __post_init__(self):
		"""Initialize use case factory"""
		self.usecases = AuthUseCaseFactory(auth_provider=self.auth_provider)

	async def login(self, request: LoginRequest) -> LoginResponse | None:
		"""
		Login a user.

		Args:
			request: Login request with email and password

		Returns:
			LoginResponse with tokens and user_id if successful, None otherwise

		Example:
			>>> request = LoginRequest(email="user@example.com", password="password123")
			>>> response = await auth_service.login(request)
			>>> if response:
			...     print(f"Access token: {response.access_token}")
		"""
		return await self.usecases.login(request)

	async def refresh(self, request: RefreshTokenRequest) -> RefreshTokenResponse | None:
		"""
		Refresh an access token.

		Args:
			request: Refresh token request

		Returns:
			RefreshTokenResponse with new access token if successful, None otherwise

		Example:
			>>> request = RefreshTokenRequest(refresh_token="...")
			>>> response = await auth_service.refresh(request)
			>>> if response:
			...     print(f"New access token: {response.access_token}")
		"""
		return await self.usecases.refresh(request)

	async def logout(self, request: LogoutRequest) -> bool:
		"""
		Logout a user by revoking their refresh token.

		Args:
			request: Logout request with refresh token

		Returns:
			True if successful, False otherwise

		Example:
			>>> request = LogoutRequest(refresh_token="...")
			>>> success = await auth_service.logout(request)
			>>> print(f"Logout {'successful' if success else 'failed'}")
		"""
		return await self.usecases.logout(request)

	async def verify(self, request: VerifyTokenRequest) -> VerifyTokenResponse:
		"""
		Verify an access token.

		Args:
			request: Verify token request with access token

		Returns:
			VerifyTokenResponse with validation result and user_id

		Example:
			>>> request = VerifyTokenRequest(access_token="eyJhbGciOi...")
			>>> response = await auth_service.verify(request)
			>>> if response.valid:
			...     print(f"Token valid for user: {response.user_id}")
		"""
		return await self.usecases.verify(request)
