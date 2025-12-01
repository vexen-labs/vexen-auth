"""
Example: Using vexen-auth with Redis cache for improved performance.

This example demonstrates:
1. Configuring vexen-auth with Redis
2. Login with automatic token caching
3. Fast token validation using Redis
4. Token refresh with cache
5. Logout with cache invalidation
"""

import asyncio

from vexen_auth.application.dto import LoginRequest, RefreshTokenRequest
from vexen_auth.core import AuthConfig, VexenAuth


async def main():
	"""
	Main example demonstrating Redis-cached authentication.
	"""
	# Configure vexen-auth with Redis cache enabled
	config = AuthConfig(
		# Database configuration
		database_url="postgresql+asyncpg://user:pass@localhost/auth_db",
		# JWT configuration
		secret_key="your-super-secret-jwt-key-change-in-production",
		algorithm="HS256",
		access_token_expires_minutes=15,  # 15 minutes
		refresh_token_expires_days=30,  # 30 days
		# Redis cache configuration (optional but recommended)
		enable_redis_cache=True,
		redis_url="redis://localhost:6379/0",  # Default Redis URL
		# If you have Redis with password:
		# redis_url="redis://:password@localhost:6379/0"
	)

	async with VexenAuth(config) as auth:
		print("=== Vexen-Auth with Redis Cache Example ===\n")

		# 1. Login (creates and caches tokens)
		print("1. Logging in user...")
		login_request = LoginRequest(email="user@example.com", password="password123")

		login_response = await auth.service.login(login_request)

		if not login_response:
			print("✗ Login failed - check credentials")
			return

		print(f"✓ Login successful!")
		print(f"  User ID: {login_response.user_id}")
		print(f"  Access Token: {login_response.access_token[:50]}...")
		print(f"  Refresh Token: {login_response.refresh_token[:50]}...")
		print()

		# 2. Verify access token (FIRST TIME - caches result in Redis)
		print("2. Verifying access token (first time - will cache)...")
		verification = await auth.service.verify_token(login_response.access_token)

		if verification.is_valid:
			print(f"✓ Token valid!")
			print(f"  User: {verification.payload.get('email')}")
			print(f"  User ID: {verification.payload.get('sub')}")
		else:
			print("✗ Token invalid")
		print()

		# 3. Verify access token again (CACHED - ultra fast!)
		print("3. Verifying access token again (from Redis cache - ~2ms)...")
		verification = await auth.service.verify_token(login_response.access_token)

		if verification.is_valid:
			print(f"✓ Token valid (from cache)!")
			print(f"  User: {verification.payload.get('email')}")
		print()

		# 4. Refresh token (uses Redis to validate refresh token)
		print("4. Refreshing access token...")
		refresh_request = RefreshTokenRequest(refresh_token=login_response.refresh_token)

		new_access_token = await auth.service.refresh_token(refresh_request)

		if new_access_token:
			print(f"✓ Token refreshed successfully!")
			print(f"  New Access Token: {new_access_token.access_token[:50]}...")
		else:
			print("✗ Token refresh failed")
		print()

		# 5. Logout (revokes tokens in both database and cache)
		print("5. Logging out (revoking tokens)...")
		logout_success = await auth.service.logout(login_response.refresh_token)

		if logout_success:
			print("✓ Logout successful - tokens revoked")
		else:
			print("✗ Logout failed")
		print()

		# 6. Try to use revoked token (should fail)
		print("6. Trying to verify revoked token...")
		verification = await auth.service.verify_token(login_response.access_token)

		if not verification.is_valid:
			print("✓ Token correctly rejected (revoked)")
		else:
			print("✗ Token still valid (unexpected)")
		print()

		print("=== Example completed ===")


async def performance_comparison():
	"""
	Compare performance with and without Redis cache.
	"""
	import time

	# Configure WITHOUT Redis
	config_no_redis = AuthConfig(
		database_url="postgresql+asyncpg://user:pass@localhost/auth_db",
		secret_key="your-secret-key",
		enable_redis_cache=False,  # No Redis
	)

	# Configure WITH Redis
	config_with_redis = AuthConfig(
		database_url="postgresql+asyncpg://user:pass@localhost/auth_db",
		secret_key="your-secret-key",
		enable_redis_cache=True,  # Redis enabled
		redis_url="redis://localhost:6379/0",
	)

	print("=== Performance Comparison ===\n")

	# Test without Redis
	async with VexenAuth(config_no_redis) as auth:
		login_req = LoginRequest(email="user@example.com", password="password123")
		login_resp = await auth.service.login(login_req)

		if login_resp:
			# Warm up
			await auth.service.verify_token(login_resp.access_token)

			# Measure 100 verifications without Redis
			start = time.perf_counter()
			for _ in range(100):
				await auth.service.verify_token(login_resp.access_token)
			no_redis_time = (time.perf_counter() - start) * 1000 / 100

			print(f"Without Redis: {no_redis_time:.2f}ms per validation")

	# Test with Redis
	async with VexenAuth(config_with_redis) as auth:
		login_req = LoginRequest(email="user@example.com", password="password123")
		login_resp = await auth.service.login(login_req)

		if login_resp:
			# Warm up cache
			await auth.service.verify_token(login_resp.access_token)

			# Measure 100 verifications with Redis (all cached)
			start = time.perf_counter()
			for _ in range(100):
				await auth.service.verify_token(login_resp.access_token)
			redis_time = (time.perf_counter() - start) * 1000 / 100

			print(f"With Redis:    {redis_time:.2f}ms per validation")
			improvement = ((no_redis_time - redis_time) / no_redis_time) * 100
			print(f"\nImprovement:   {improvement:.1f}% faster with Redis ✓")


if __name__ == "__main__":
	# Run basic example
	asyncio.run(main())

	# Uncomment to run performance comparison
	# asyncio.run(performance_comparison())
