"""Logout use case."""

from dataclasses import dataclass

from vexen_auth.application.dto.auth_dto import LogoutRequest
from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort


@dataclass
class LogoutUseCase:
	"""Use case for user logout"""

	auth_provider: IAuthProviderPort

	async def __call__(self, request: LogoutRequest) -> bool:
		"""
		Execute logout use case.

		Args:
			request: Logout request with refresh token to revoke

		Returns:
			True if successful, False otherwise
		"""
		return await self.auth_provider.revoke_token(request.refresh_token)
