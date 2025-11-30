"""Login use case."""

from dataclasses import dataclass

from vexen_auth.application.dto.auth_dto import LoginRequest, LoginResponse
from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort


@dataclass
class LoginUseCase:
	"""Use case for user login"""

	auth_provider: IAuthProviderPort

	async def __call__(self, request: LoginRequest) -> LoginResponse | None:
		"""
		Execute login use case.

		Args:
			request: Login request with email and password

		Returns:
			LoginResponse with tokens and user_id if successful, None otherwise
		"""
		result = await self.auth_provider.authenticate(request.email, request.password)

		if not result:
			return None

		access_token, refresh_token, user_id = result

		return LoginResponse(
			access_token=access_token, refresh_token=refresh_token, user_id=user_id
		)
