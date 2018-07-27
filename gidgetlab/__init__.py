"""An async GitLab API library"""

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

# flake8: noqa: F401
from .exceptions import (
    GitLabException,
    ValidationFailure,
    HTTPException,
    RedirectionException,
    BadRequest,
    RateLimitExceeded,
    InvalidField,
    GitLabBroken,
)
