"""
Example usage of VexenAuth with OpenID Connect.

This example demonstrates how to integrate OpenID Connect authentication
with providers like Google, Azure AD, Keycloak, etc.
"""

import asyncio

from vexen_auth import VexenAuth
from vexen_auth.application.dto import (
	OpenIDAuthRequest,
	OpenIDCallbackRequest,
)
from vexen_auth.core import AuthConfig


async def main():
	"""Example demonstrating OpenID Connect authentication flow"""

	# Configuration with OpenID Connect providers
	config = AuthConfig(
		database_url="sqlite+aiosqlite:///./vexen_auth.db",
		secret_key="your-super-secret-key-change-in-production",
		access_token_expires_minutes=15,
		refresh_token_expires_days=30,
		# Configure OpenID Connect providers
		openid_providers={
			# Google OpenID Connect
			"google": {
				"name": "google",
				"client_id": "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com",
				"client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
				"discovery_url": "https://accounts.google.com/.well-known/openid-configuration",
				"redirect_uri": "http://localhost:8000/auth/callback/google",
				"scopes": ["openid", "email", "profile"],
				"enabled": True,
			},
			# Azure AD / Microsoft Entra ID
			"azure": {
				"name": "azure",
				"client_id": "YOUR_AZURE_CLIENT_ID",
				"client_secret": "YOUR_AZURE_CLIENT_SECRET",
				"discovery_url": "https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0/.well-known/openid-configuration",
				"redirect_uri": "http://localhost:8000/auth/callback/azure",
				"scopes": ["openid", "email", "profile"],
				"enabled": False,  # Disabled for this example
			},
			# Keycloak
			"keycloak": {
				"name": "keycloak",
				"client_id": "YOUR_KEYCLOAK_CLIENT_ID",
				"client_secret": "YOUR_KEYCLOAK_CLIENT_SECRET",
				"discovery_url": "https://your-keycloak-domain/realms/your-realm/.well-known/openid-configuration",
				"redirect_uri": "http://localhost:8000/auth/callback/keycloak",
				"scopes": ["openid", "email", "profile"],
				"enabled": False,  # Disabled for this example
			},
		},
	)

	# Initialize VexenAuth
	async with VexenAuth(config) as auth:
		print("=" * 80)
		print("VexenAuth - OpenID Connect Example")
		print("=" * 80)

		# Step 1: Initiate OpenID Connect authentication
		print("\n1. Initiating OpenID Connect authentication with Google...")
		print("-" * 80)

		auth_request = OpenIDAuthRequest(
			provider="google",
			state="random-state-for-csrf-protection",  # In production, generate a secure random state
		)

		auth_response = await auth.openid.initiate_auth(auth_request)

		if auth_response:
			print(f"✅ Authorization URL generated:")
			print(f"   URL: {auth_response.authorization_url}")
			print(f"   State: {auth_response.state}")
			print(f"   Provider: {auth_response.provider}")
			print("\n   👉 In a real application, redirect the user to this URL")
			print("   👉 The user will authenticate with Google and be redirected back")
		else:
			print("❌ Failed to initiate authentication")
			return

		# Step 2: Handle OAuth callback (simulated)
		print("\n2. Handling OAuth callback...")
		print("-" * 80)
		print("   ℹ️  In a real application, this would be triggered by the OAuth redirect")
		print("   ℹ️  The authorization code would come from the URL parameters")

		# Simulate receiving an authorization code
		# In a real app, this would come from the OAuth callback URL
		# For this example, we'll skip the actual OAuth flow
		print("\n   ⚠️  Skipping actual OAuth flow for this example")
		print("   ⚠️  In production, you would:")
		print("      1. User clicks the authorization URL")
		print("      2. User authenticates with the provider")
		print("      3. Provider redirects to your callback URL with 'code' parameter")
		print("      4. Your app calls auth.openid.handle_callback()")

		# Example of how you would handle the callback in production:
		"""
		callback_request = OpenIDCallbackRequest(
			code="AUTHORIZATION_CODE_FROM_PROVIDER",
			state=auth_response.state,
			provider="google"
		)

		login_response = await auth.openid.handle_callback(callback_request)

		if login_response:
			print(f"✅ User authenticated successfully!")
			print(f"   User ID: {login_response.user_id}")
			print(f"   Email: {login_response.email}")
			print(f"   Name: {login_response.name}")
			print(f"   Access Token: {login_response.access_token[:20]}...")
			print(f"   Refresh Token: {login_response.refresh_token[:20]}...")

			# Store tokens securely (e.g., in HTTP-only cookies)
			access_token = login_response.access_token
			refresh_token = login_response.refresh_token

			# Step 3: Verify the access token
			print("\n3. Verifying access token...")
			print("-" * 80)

			token_payload = await auth.openid.verify_token("google", access_token)

			if token_payload:
				print(f"✅ Token is valid!")
				print(f"   User ID: {token_payload['sub']}")
				print(f"   Email: {token_payload['email']}")
			else:
				print("❌ Token is invalid or expired")

			# Step 4: Refresh the access token
			print("\n4. Refreshing access token...")
			print("-" * 80)

			new_access_token = await auth.openid.refresh_token("google", refresh_token)

			if new_access_token:
				print(f"✅ Token refreshed successfully!")
				print(f"   New Access Token: {new_access_token[:20]}...")
			else:
				print("❌ Failed to refresh token")

			# Step 5: Logout
			print("\n5. Logging out...")
			print("-" * 80)

			logout_success = await auth.openid.logout("google", refresh_token)

			if logout_success:
				print("✅ User logged out successfully!")
			else:
				print("❌ Failed to logout")
		"""

		# Integration with FastAPI example
		print("\n" + "=" * 80)
		print("FastAPI Integration Example")
		print("=" * 80)
		print("""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/auth/login/{provider}")
async def login(provider: str):
	\"\"\"Initiate OpenID Connect login\"\"\"
	auth_request = OpenIDAuthRequest(provider=provider)
	auth_response = await auth.openid.initiate_auth(auth_request)

	if not auth_response:
		raise HTTPException(status_code=400, detail="Invalid provider")

	# Store state in session for CSRF protection
	# session["oauth_state"] = auth_response.state

	return RedirectResponse(url=auth_response.authorization_url)

@app.get("/auth/callback/{provider}")
async def callback(provider: str, code: str, state: str):
	\"\"\"Handle OpenID Connect callback\"\"\"
	# Verify state for CSRF protection
	# if state != session.get("oauth_state"):
	#     raise HTTPException(status_code=400, detail="Invalid state")

	callback_request = OpenIDCallbackRequest(
		code=code,
		state=state,
		provider=provider
	)

	login_response = await auth.openid.handle_callback(callback_request)

	if not login_response:
		raise HTTPException(status_code=401, detail="Authentication failed")

	# Set tokens in HTTP-only cookies
	response = RedirectResponse(url="/dashboard")
	response.set_cookie(
		key="access_token",
		value=login_response.access_token,
		httponly=True,
		secure=True,
		samesite="lax"
	)
	response.set_cookie(
		key="refresh_token",
		value=login_response.refresh_token,
		httponly=True,
		secure=True,
		samesite="lax"
	)

	return response

@app.get("/auth/logout")
async def logout(request: Request):
	\"\"\"Logout user\"\"\"
	refresh_token = request.cookies.get("refresh_token")

	if refresh_token:
		await auth.openid.logout("google", refresh_token)

	response = RedirectResponse(url="/")
	response.delete_cookie("access_token")
	response.delete_cookie("refresh_token")

	return response

@app.get("/api/protected")
async def protected_route(request: Request):
	\"\"\"Protected route that requires authentication\"\"\"
	access_token = request.cookies.get("access_token")

	if not access_token:
		raise HTTPException(status_code=401, detail="Not authenticated")

	token_payload = await auth.openid.verify_token("google", access_token)

	if not token_payload:
		raise HTTPException(status_code=401, detail="Invalid token")

	return {
		"message": "Access granted",
		"user_id": token_payload["sub"],
		"email": token_payload["email"]
	}
		""")

		print("\n" + "=" * 80)
		print("Configuration Notes")
		print("=" * 80)
		print("""
1. Google OAuth Setup:
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URI: http://localhost:8000/auth/callback/google

2. Azure AD Setup:
   - Go to https://portal.azure.com/
   - Navigate to Azure Active Directory > App registrations
   - Register a new application
   - Add redirect URI: http://localhost:8000/auth/callback/azure
   - Generate client secret in Certificates & secrets

3. Keycloak Setup:
   - Access your Keycloak admin console
   - Create or select a realm
   - Create a new client
   - Configure redirect URIs
   - Set client authentication to enabled
   - Copy client ID and secret

4. Security Best Practices:
   - Always use HTTPS in production
   - Use HTTP-only cookies for tokens
   - Implement CSRF protection with state parameter
   - Store client secrets securely (environment variables, secret managers)
   - Implement rate limiting on auth endpoints
   - Use short-lived access tokens (15-30 minutes)
   - Rotate refresh tokens regularly
		""")

		print("\n" + "=" * 80)
		print("✅ Example completed successfully!")
		print("=" * 80)


if __name__ == "__main__":
	asyncio.run(main())
