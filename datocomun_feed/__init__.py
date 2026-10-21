"""Cliente Python para Recuento API (Dato Común)."""

from .client import AuthError, FeedClient, FeedError, NoEncontrado
from .models import Candidatura, Circunscripcion

__all__ = [
    "FeedClient",
    "FeedError",
    "AuthError",
    "NoEncontrado",
    "Candidatura",
    "Circunscripcion",
]
__version__ = "0.1.0"
