"""Refresh token use case."""

from dataclasses import dataclass

from vexen_auth.application.dto.auth_dto import RefreshTokenRequest, RefreshTokenResponse
from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort


@dataclass
class RefreshTokenUseCase:
	"""Use case for refreshing access tokens"""

	auth_provider: IAuthProviderPort

	async def __call__(self, request: RefreshTokenRequest) -> RefreshTokenResponse | None:
		"""
		Execute refresh token use case.

		Args:
			request: Refresh token request

		Returns:
			RefreshTokenResponse with new access token if successful, None otherwise
		"""
		access_token = await self.auth_provider.refresh_token(request.refresh_token)

		if not access_token:
			return None

		return RefreshTokenResponse(access_token=access_token)
