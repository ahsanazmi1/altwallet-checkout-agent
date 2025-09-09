"""
Compatibility shim for AltWallet Checkout Agent.

This module provides backward compatibility for the old 'altwallet_agent' package name.
All imports and references are redirected to the new 'orca_checkout' package.

DEPRECATED: This module will be removed in a future version.
Please update your imports to use 'orca_checkout' instead of 'altwallet_agent'.
"""

import warnings
import sys
from pathlib import Path

# Add the src directory to the path so we can import the actual module
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import everything from the actual module
try:
    from altwallet_agent import *
    from altwallet_agent import __version__, __author__, __email__
except ImportError as e:
    # If the actual module doesn't exist yet, provide a helpful error
    raise ImportError(
        "The altwallet_agent module has been renamed to orca_checkout. "
        "Please update your imports to use 'from orca_checkout import ...' "
        "instead of 'from altwallet_agent import ...'"
    ) from e

# Issue deprecation warning
warnings.warn(
    "The 'altwallet_agent' package has been renamed to 'orca_checkout'. "
    "Please update your imports to use 'orca_checkout' instead. "
    "This compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export the module for backward compatibility
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "CheckoutAgent",
    "CheckoutRequest",
    "CheckoutResponse", 
    "ScoreRequest",
    "ScoreResponse",
    "ScoreResult",
    "score_transaction"
]
