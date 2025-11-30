"""Verify token use case."""

from dataclasses import dataclass

from vexen_auth.application.dto.auth_dto import VerifyTokenRequest, VerifyTokenResponse
from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort


@dataclass
class VerifyTokenUseCase:
	"""Use case for verifying access tokens"""

	auth_provider: IAuthProviderPort

	async def __call__(self, request: VerifyTokenRequest) -> VerifyTokenResponse:
		"""
		Execute verify token use case.

		Args:
			request: Verify token request

		Returns:
			VerifyTokenResponse with validation result and user_id
		"""
		# Verify access token
		payload = await self.auth_provider.verify_access_token(request.access_token)

		if not payload:
			return VerifyTokenResponse(valid=False, user_id=None)

		# Get user_id from payload
		user_id = payload.get("sub")

		return VerifyTokenResponse(valid=True, user_id=user_id)
