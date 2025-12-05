"""OpenID Connect authentication service."""

from vexen_auth.application.dto.openid_dto import (
	OpenIDAuthRequest,
	OpenIDAuthResponse,
	OpenIDCallbackRequest,
	OpenIDLoginResponse,
)
from vexen_auth.infraestructure.provider.openid_provider import OpenIDProvider


class OpenIDService:
	"""Service for OpenID Connect authentication operations"""

	def __init__(self, providers: dict[str, OpenIDProvider]):
		"""
		Initialize OpenID service.

		Args:
			providers: Dictionary of provider name to OpenIDProvider instance
		"""
		self.providers = providers

	def get_provider(self, provider_name: str) -> OpenIDProvider | None:
		"""
		Get an OpenID provider by name.

		Args:
			provider_name: Name of the provider

		Returns:
			OpenIDProvider instance or None if not found
		"""
		return self.providers.get(provider_name)

	async def initiate_auth(self, request: OpenIDAuthRequest) -> OpenIDAuthResponse | None:
		"""
		Initiate OpenID Connect authentication flow.

		Args:
			request: OpenID auth request with optional state

		Returns:
			OpenIDAuthResponse with authorization URL and state
		"""
		provider = self.get_provider(request.provider)
		if not provider:
			return None

		try:
			authorization_url, state = provider.get_authorization_url(request.state)

			return OpenIDAuthResponse(
				authorization_url=authorization_url,
				state=state,
				provider=request.provider,
			)
		except Exception:
			return None

	async def handle_callback(
		self, request: OpenIDCallbackRequest
	) -> OpenIDLoginResponse | None:
		"""
		Handle OpenID Connect callback and complete authentication.

		Args:
			request: Callback request with authorization code

		Returns:
			OpenIDLoginResponse with tokens and user info, or None if failed
		"""
		provider = self.get_provider(request.provider)
		if not provider:
			return None

		try:
			result = await provider.authenticate_with_code(request.code)
			if not result:
				return None

			access_token, refresh_token, user_id, user_info = result

			return OpenIDLoginResponse(
				access_token=access_token,
				refresh_token=refresh_token,
				user_id=user_id,
				email=user_info.get("email", ""),
				name=user_info.get("name"),
				provider=request.provider,
			)
		except Exception:
			return None

	async def refresh_token(self, provider_name: str, refresh_token: str) -> str | None:
		"""
		Refresh an access token.

		Args:
			provider_name: Name of the provider
			refresh_token: Refresh token

		Returns:
			New access token or None if failed
		"""
		provider = self.get_provider(provider_name)
		if not provider:
			return None

		return await provider.refresh_token(refresh_token)

	async def logout(self, provider_name: str, refresh_token: str) -> bool:
		"""
		Logout user by revoking refresh token.

		Args:
			provider_name: Name of the provider
			refresh_token: Refresh token to revoke

		Returns:
			True if successful, False otherwise
		"""
		provider = self.get_provider(provider_name)
		if not provider:
			return False

		return await provider.revoke_token(refresh_token)

	async def verify_token(self, provider_name: str, access_token: str) -> dict | None:
		"""
		Verify an access token.

		Args:
			provider_name: Name of the provider
			access_token: Access token to verify

		Returns:
			Token payload if valid, None otherwise
		"""
		provider = self.get_provider(provider_name)
		if not provider:
			return None

		return await provider.verify_access_token(access_token)
