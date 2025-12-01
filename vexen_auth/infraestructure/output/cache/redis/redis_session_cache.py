"""Redis implementation of session cache."""

import json
from datetime import timedelta

import redis.asyncio as redis

from vexen_auth.domain.repository.session_cache_port import ISessionCachePort


class RedisSessionCache(ISessionCachePort):
	"""
	Redis implementation for session and token caching.

	This adapter provides fast in-memory caching for:
	- Access tokens validation data
	- Refresh tokens
	- User sessions
	- Token revocation tracking

	This significantly improves performance by reducing database queries
	for frequently validated tokens.
	"""

	def __init__(self, redis_url: str = "redis://localhost:6379/0"):
		"""
		Initialize Redis session cache.

		Args:
			redis_url: Redis connection URL
				Format: redis://[:password]@host[:port][/db]
				Examples:
					- redis://localhost:6379/0
					- redis://:password@localhost:6379/1
					- redis://redis-host:6380/0
		"""
		self.redis_url = redis_url
		self._client: redis.Redis | None = None

	async def _get_client(self) -> redis.Redis:
		"""Get or create Redis client."""
		if self._client is None:
			self._client = await redis.from_url(
				self.redis_url,
				encoding="utf-8",
				decode_responses=True,
			)
		return self._client

	def _access_token_key(self, token_hash: str) -> str:
		"""Generate Redis key for access token."""
		return f"access_token:{token_hash}"

	def _refresh_token_key(self, token_hash: str) -> str:
		"""Generate Redis key for refresh token."""
		return f"refresh_token:{token_hash}"

	def _user_session_key(self, user_id: str) -> str:
		"""Generate Redis key for user session."""
		return f"user_session:{user_id}"

	def _revoked_token_key(self, token_hash: str) -> str:
		"""Generate Redis key for revoked token."""
		return f"revoked:{token_hash}"

	def _user_tokens_key(self, user_id: str) -> str:
		"""Generate Redis key for user's token set."""
		return f"user_tokens:{user_id}"

	async def set_access_token(
		self, token_hash: str, user_data: dict, expires_in: timedelta
	) -> None:
		"""
		Cache an access token with associated user data.

		Args:
			token_hash: Hashed access token value
			user_data: User information associated with the token
			expires_in: Time until token expires
		"""
		client = await self._get_client()
		key = self._access_token_key(token_hash)
		value = json.dumps(user_data)

		await client.setex(
			key,
			int(expires_in.total_seconds()),
			value,
		)

		# Track this token for the user
		user_id = user_data.get("sub")
		if user_id:
			await client.sadd(self._user_tokens_key(user_id), token_hash)

	async def get_access_token(self, token_hash: str) -> dict | None:
		"""
		Retrieve cached access token data.

		Args:
			token_hash: Hashed access token value

		Returns:
			User data if token is cached and valid, None otherwise
		"""
		client = await self._get_client()

		# Check if token is revoked
		if await self.is_token_revoked(token_hash):
			return None

		key = self._access_token_key(token_hash)
		value = await client.get(key)

		if not value:
			return None

		try:
			return json.loads(value)
		except json.JSONDecodeError:
			return None

	async def revoke_access_token(self, token_hash: str) -> None:
		"""
		Revoke a cached access token.

		Args:
			token_hash: Hashed access token value
		"""
		client = await self._get_client()

		# Get TTL of the access token to set revocation expiry
		access_key = self._access_token_key(token_hash)
		ttl = await client.ttl(access_key)

		# Delete the cached token
		await client.delete(access_key)

		# Mark as revoked for the remaining time
		if ttl > 0:
			revoked_key = self._revoked_token_key(token_hash)
			await client.setex(revoked_key, ttl, "1")

	async def set_refresh_token(self, token_hash: str, user_id: str, expires_in: timedelta) -> None:
		"""
		Cache a refresh token.

		Args:
			token_hash: Hashed refresh token value
			user_id: ID of the user this token belongs to
			expires_in: Time until token expires
		"""
		client = await self._get_client()
		key = self._refresh_token_key(token_hash)

		await client.setex(
			key,
			int(expires_in.total_seconds()),
			user_id,
		)

		# Track this token for the user
		await client.sadd(self._user_tokens_key(user_id), token_hash)

	async def get_refresh_token(self, token_hash: str) -> str | None:
		"""
		Retrieve cached refresh token user ID.

		Args:
			token_hash: Hashed refresh token value

		Returns:
			User ID if token is cached and valid, None otherwise
		"""
		client = await self._get_client()

		# Check if token is revoked
		if await self.is_token_revoked(token_hash):
			return None

		key = self._refresh_token_key(token_hash)
		return await client.get(key)

	async def revoke_refresh_token(self, token_hash: str) -> None:
		"""
		Revoke a cached refresh token.

		Args:
			token_hash: Hashed refresh token value
		"""
		client = await self._get_client()

		# Get TTL of the refresh token to set revocation expiry
		refresh_key = self._refresh_token_key(token_hash)
		ttl = await client.ttl(refresh_key)

		# Delete the cached token
		await client.delete(refresh_key)

		# Mark as revoked for the remaining time
		if ttl > 0:
			revoked_key = self._revoked_token_key(token_hash)
			await client.setex(revoked_key, ttl, "1")

	async def revoke_all_user_tokens(self, user_id: str) -> None:
		"""
		Revoke all cached tokens for a user.

		Args:
			user_id: User ID
		"""
		client = await self._get_client()

		# Get all tokens for this user
		user_tokens_key = self._user_tokens_key(user_id)
		token_hashes = await client.smembers(user_tokens_key)

		# Revoke each token
		for token_hash in token_hashes:
			# Check if it's an access or refresh token and revoke accordingly
			access_key = self._access_token_key(token_hash)
			refresh_key = self._refresh_token_key(token_hash)

			access_ttl = await client.ttl(access_key)
			refresh_ttl = await client.ttl(refresh_key)

			if access_ttl > 0:
				await client.delete(access_key)
				revoked_key = self._revoked_token_key(token_hash)
				await client.setex(revoked_key, access_ttl, "1")

			if refresh_ttl > 0:
				await client.delete(refresh_key)
				revoked_key = self._revoked_token_key(token_hash)
				await client.setex(revoked_key, refresh_ttl, "1")

		# Clear the user tokens set
		await client.delete(user_tokens_key)

	async def is_token_revoked(self, token_hash: str) -> bool:
		"""
		Check if a token has been revoked.

		Args:
			token_hash: Hashed token value

		Returns:
			True if token is revoked, False otherwise
		"""
		client = await self._get_client()
		revoked_key = self._revoked_token_key(token_hash)
		return await client.exists(revoked_key) > 0

	async def set_user_session(
		self, user_id: str, session_data: dict, expires_in: timedelta
	) -> None:
		"""
		Cache user session data.

		Args:
			user_id: User ID
			session_data: Session information to cache
			expires_in: Time until session expires
		"""
		client = await self._get_client()
		key = self._user_session_key(user_id)
		value = json.dumps(session_data)

		await client.setex(
			key,
			int(expires_in.total_seconds()),
			value,
		)

	async def get_user_session(self, user_id: str) -> dict | None:
		"""
		Retrieve cached user session data.

		Args:
			user_id: User ID

		Returns:
			Session data if cached and valid, None otherwise
		"""
		client = await self._get_client()
		key = self._user_session_key(user_id)
		value = await client.get(key)

		if not value:
			return None

		try:
			return json.loads(value)
		except json.JSONDecodeError:
			return None

	async def delete_user_session(self, user_id: str) -> None:
		"""
		Delete user session data.

		Args:
			user_id: User ID
		"""
		client = await self._get_client()
		key = self._user_session_key(user_id)
		await client.delete(key)

	async def close(self) -> None:
		"""Close Redis connections."""
		if self._client:
			await self._client.aclose()
			self._client = None
