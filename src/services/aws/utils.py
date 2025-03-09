import logging
import functools
import time
from typing import Callable, Any

import boto3
from src.core.constants import (
    SSO_ENTITLMENTS_APP_NAME,
    MAX_RETRIES,
    RETRY_DELAY_SECONDS,
)

logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
sso_admin_client = boto3.client("sso-admin")
aws_organizations_client = boto3.client("organizations")


def handle_aws_exceptions(
    max_retries: int = MAX_RETRIES,
    retry_delay_seconds: float = RETRY_DELAY_SECONDS,
    retryable_exceptions: tuple = (
        sso_admin_client.exceptions.InternalServerException,
        sso_admin_client.exceptions.ConflictException,
        sso_admin_client.exceptions.ThrottlingException,
        aws_organizations_client.exceptions.ServiceException,
        aws_organizations_client.exceptions.TooManyRequestsException,
    ),
) -> Callable:
    """
    Decorator to handle AWS Organizations API exceptions with retry logic.

    Parameters:
    -----------
    max_retries: int
        Maximum number of retry attempts
    retry_delay: float
        Delay in seconds between retries (will be exponentially increased)
    retryable_exceptions: tuple
        Tuple of exceptions that should trigger a retry

    Returns:
    --------
    Callable
        The wrapped function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            retries = 0
            while True:
                try:
                    return func(self, *args, **kwargs)

                except retryable_exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded: {e}")
                        raise e

                    wait_time = retry_delay_seconds * (2 ** (retries - 1))  # Exponential backoff
                    logger.warning(f"Retryable error occurred: {e}. " f"Attempt {retries}/{max_retries}. " f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                # AWS Organizations related exceptions
                except aws_organizations_client.exceptions.ParentNotFoundException as e:
                    logger.error(f"Invalid parent OU name: {e}")
                    raise e
                except aws_organizations_client.exceptions.AccessDeniedException as e:
                    logger.error(f"Missing required IAM policy permissions: {e}")
                    raise e

                # AWS SSO Admin related exceptions
                except sso_admin_client.exceptions.AccessDeniedException as e:
                    logger.error(f"Missing required IAM policy permissions: {e}")
                    raise e
                except sso_admin_client.exceptions.ServiceQuotaExceededException as e:
                    logger.error(f"Exceeded limit of allowed AWS account assignments, " f"request service quota increase: {e}")
                    raise e
                except sso_admin_client.exceptions.ResourceNotFoundException as e:
                    logger.error(f"Invalid TargetID, PrincipalID, or PermissionSetArn: {e}")
                    raise e

        return wrapper

    return decorator

