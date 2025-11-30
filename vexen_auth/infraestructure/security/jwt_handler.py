"""JWT token generation and validation."""

import hashlib
from datetime import datetime, timedelta
from typing import Any

import jwt


class JWTHandler:
	"""Handle JWT token operations"""

	def __init__(self, secret_key: str, algorithm: str = "HS256"):
		"""
		Initialize JWT handler.

		Args:
			secret_key: Secret key for signing tokens
			algorithm: JWT algorithm (default: HS256)
		"""
		self.secret_key = secret_key
		self.algorithm = algorithm

	def create_access_token(
		self, data: dict[str, Any], expires_delta: timedelta | None = None
	) -> str:
		"""
		Create an access token.

		Args:
			data: Data to encode in the token
			expires_delta: Token expiration time (default: 15 minutes)

		Returns:
			JWT access token string
		"""
		to_encode = data.copy()
		if expires_delta:
			expire = datetime.utcnow() + expires_delta
		else:
			expire = datetime.utcnow() + timedelta(minutes=15)

		to_encode.update({"exp": expire, "type": "access"})
		encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
		return encoded_jwt

	def create_refresh_token(
		self, data: dict[str, Any], expires_delta: timedelta | None = None
	) -> str:
		"""
		Create a refresh token.

		Args:
			data: Data to encode in the token
			expires_delta: Token expiration time (default: 30 days)

		Returns:
			JWT refresh token string
		"""
		to_encode = data.copy()
		if expires_delta:
			expire = datetime.utcnow() + expires_delta
		else:
			expire = datetime.utcnow() + timedelta(days=30)

		to_encode.update({"exp": expire, "type": "refresh"})
		encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
		return encoded_jwt

	def decode_token(self, token: str) -> dict[str, Any]:
		"""
		Decode and validate a JWT token.

		Args:
			token: JWT token to decode

		Returns:
			Decoded token payload

		Raises:
			jwt.ExpiredSignatureError: If token is expired
			jwt.InvalidTokenError: If token is invalid
		"""
		payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
		return payload

	def verify_token(self, token: str) -> tuple[bool, dict[str, Any] | None]:
		"""
		Verify a JWT token.

		Args:
			token: JWT token to verify

		Returns:
			Tuple of (is_valid, payload)
		"""
		try:
			payload = self.decode_token(token)
			return True, payload
		except jwt.ExpiredSignatureError:
			return False, None
		except jwt.InvalidTokenError:
			return False, None

	@staticmethod
	def hash_token(token: str) -> str:
		"""
		Hash a token for storage.

		Args:
			token: Token to hash

		Returns:
			Hashed token (SHA-256)
		"""
		return hashlib.sha256(token.encode()).hexdigest()
