"""Cliente Python para Recuento API (Dato Común)."""

from .client import AuthError, FeedClient, FeedError

__all__ = ["FeedClient", "FeedError", "AuthError"]
__version__ = "0.1.0"
