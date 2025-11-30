"""Factory for auth use cases."""

from dataclasses import dataclass, field

from vexen_auth.domain.provider.auth_provider_port import IAuthProviderPort

from .login_usecase import LoginUseCase
from .logout_usecase import LogoutUseCase
from .refresh_token_usecase import RefreshTokenUseCase
from .verify_token_usecase import VerifyTokenUseCase


@dataclass
class AuthUseCaseFactory:
	"""Factory for creating auth use cases"""

	auth_provider: IAuthProviderPort

	login: LoginUseCase = field(init=False)
	refresh: RefreshTokenUseCase = field(init=False)
	logout: LogoutUseCase = field(init=False)
	verify: VerifyTokenUseCase = field(init=False)

	def __post_init__(self):
		"""Initialize all use cases"""
		self.login = LoginUseCase(auth_provider=self.auth_provider)
		self.refresh = RefreshTokenUseCase(auth_provider=self.auth_provider)
		self.logout = LogoutUseCase(auth_provider=self.auth_provider)
		self.verify = VerifyTokenUseCase(auth_provider=self.auth_provider)
