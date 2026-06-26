"""
Reevaluation Time Exercise - Flask Blueprint sub-package.

This module is registered as a Blueprint by the main app's create_app(),
NOT run as a standalone Flask application.
"""

import logging

# Configure logging for this sub-package
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

from .routes import bp  # noqa: F401, E402
