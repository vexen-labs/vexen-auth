"""Base DTOs and response structures."""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class BaseResponse(Generic[T]):
	"""
	Generic response wrapper.

	Attributes:
		success: Whether the operation was successful
		data: The response data (if successful)
		error: Error message (if failed)
		message: Optional message
	"""

	success: bool
	data: T | None = None
	error: str | None = None
	message: str | None = None

	@classmethod
	def ok(cls, data: T, message: str | None = None) -> "BaseResponse[T]":
		"""Create a successful response"""
		return cls(success=True, data=data, error=None, message=message)

	@classmethod
	def fail(cls, error: str) -> "BaseResponse[T]":
		"""Create a failed response"""
		return cls(success=False, data=None, error=error)
