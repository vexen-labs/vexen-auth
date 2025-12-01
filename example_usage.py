"""Example usage of VexenAuth."""

import asyncio

from vexen_auth import (
	AuthConfig,
	LoginRequest,
	LogoutRequest,
	RefreshTokenRequest,
	VexenAuth,
)


async def main():
	"""Example usage of VexenAuth"""

	# Configure VexenAuth
	config = AuthConfig(
		database_url="postgresql+asyncpg://user:password@localhost:5432/vexen_auth",
		secret_key="your-secret-key-change-in-production",
		algorithm="HS256",
		access_token_expires_minutes=15,
		refresh_token_expires_days=30,
		# Note: user_repository and role_repository should be provided
		# for integration with vexen-user and vexen-rbac
		# For this example, we assume they're configured elsewhere
	)

	# Use VexenAuth with context manager
	async with VexenAuth(config) as auth:
		print("VexenAuth initialized successfully!")

		# Example 1: Login
		print("\n--- Login Example ---")
		login_request = LoginRequest(
			email="user@example.com",
			password="SecurePassword123",
		)

		login_response = await auth.service.login(login_request)

		if login_response:
			print("Login successful!")
			print(f"Access Token: {login_response.access_token[:50]}...")
			print(f"Refresh Token: {login_response.refresh_token[:50]}...")
			print(f"User: {login_response.user.name} ({login_response.user.email})")
			print(f"Role: {login_response.user.role.display_name}")
			print(f"Permissions: {login_response.user.role.permissions}")

			# Save tokens for later examples
			access_token = login_response.access_token
			refresh_token = login_response.refresh_token
		else:
			print("Login failed! Invalid credentials.")
			return

		await auth.commit()

		# Example 2: Get current user info (verify token)
		print("\n--- Verify Token (Me) Example ---")
		me_response = await auth.service.me(access_token)

		if me_response:
			print("Token valid!")
			print(f"User: {me_response.name} ({me_response.email})")
			print(f"Role: {me_response.role.display_name}")
		else:
			print("Token invalid or expired!")

		# Example 3: Refresh access token
		print("\n--- Refresh Token Example ---")
		refresh_request = RefreshTokenRequest(refresh_token=refresh_token)
		refresh_response = await auth.service.refresh(refresh_request)

		if refresh_response:
			print("Token refreshed successfully!")
			print(f"New Access Token: {refresh_response.access_token[:50]}...")
			access_token = refresh_response.access_token
		else:
			print("Token refresh failed!")

		# Example 4: Logout
		print("\n--- Logout Example ---")
		logout_request = LogoutRequest(refresh_token=refresh_token)
		logout_success = await auth.service.logout(logout_request)

		if logout_success:
			print("Logout successful! Refresh token revoked.")
		else:
			print("Logout failed!")

		await auth.commit()

		# Verify token is revoked
		print("\n--- Verify Token After Logout ---")
		refresh_request = RefreshTokenRequest(refresh_token=refresh_token)
		refresh_response = await auth.service.refresh(refresh_request)

		if refresh_response:
			print("Warning: Token still valid after logout!")
		else:
			print("Confirmed: Refresh token is revoked.")


if __name__ == "__main__":
	asyncio.run(main())
