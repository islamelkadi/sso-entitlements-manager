"""
AWS Service Exception Handling Utility

This module provides a decorator for robust error handling and retry mechanisms 
for AWS Organizations and SSO Admin API calls. It implements intelligent retry 
strategies with exponential backoff and comprehensive exception logging.

Key Features:
    - Automatic retry for transient AWS service exceptions
    - Exponential backoff between retry attempts
    - Detailed logging of errors and retry attempts
    - Configurable retry parameters
    - Specialized handling for AWS Organizations and SSO Admin exceptions
"""

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

# Define constants
LOGGER = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
SSO_ADMIN_CLIENT = boto3.client("sso-admin")
AWS_ORGANIZATIONS_CLIENT = boto3.client("organizations")


# Define functions
def handle_aws_exceptions(
    max_retries: int = MAX_RETRIES,
    retry_delay_seconds: float = RETRY_DELAY_SECONDS,
    retryable_exceptions: tuple = (
        SSO_ADMIN_CLIENT.exceptions.InternalServerException,
        SSO_ADMIN_CLIENT.exceptions.ConflictException,
        SSO_ADMIN_CLIENT.exceptions.ThrottlingException,
        AWS_ORGANIZATIONS_CLIENT.exceptions.ServiceException,
        AWS_ORGANIZATIONS_CLIENT.exceptions.TooManyRequestsException,
    ),
) -> Callable:
    """
    A decorator that provides robust exception handling and retry mechanism for AWS service calls.

    This decorator wraps methods to handle common AWS service exceptions, implementing
    an intelligent retry strategy with exponential backoff. It can handle transient
    service errors, throttling, and other recoverable exceptions.

    Args:
        max_retries (int, optional): Maximum number of retry attempts before giving up.
            Defaults to MAX_RETRIES from constants.
        retry_delay_seconds (float, optional): Initial delay between retry attempts.
            The delay increases exponentially with each retry. Defaults to RETRY_DELAY_SECONDS.
        retryable_exceptions (tuple, optional): A tuple of exception types that trigger
            a retry attempt. Defaults to common AWS service exceptions.

    Returns:
        Callable: A decorator that can be applied to methods to add retry and exception handling.

    Raises:
        Various AWS service-specific exceptions after max retries are exhausted, including:
        - ParentNotFoundException
        - AccessDeniedException
        - ServiceQuotaExceededException
        - ResourceNotFoundException

    Examples:
        @handle_aws_exceptions()
        def list_aws_accounts(self):
            # Method implementation that might throw AWS service exceptions
            return organizations_client.list_accounts()
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
                        # Lazy formatting using %r for safe representation
                        LOGGER.error("Max retries (%d) exceeded: %r", max_retries, e)
                        raise e

                    wait_time = retry_delay_seconds * (
                        2 ** (retries - 1)
                    )  # Exponential backoff
                    # Lazy formatting for warning log
                    LOGGER.warning(
                        "Retryable error occurred: %r. Attempt %d/%d. Retrying in %f seconds...",
                        e,
                        retries,
                        max_retries,
                        wait_time,
                    )
                    time.sleep(wait_time)
                    continue

                # AWS Organizations related exceptions
                except AWS_ORGANIZATIONS_CLIENT.exceptions.ParentNotFoundException as e:
                    # Lazy formatting for error log
                    LOGGER.error("Invalid parent OU name: %r", e)
                    raise e
                except AWS_ORGANIZATIONS_CLIENT.exceptions.AccessDeniedException as e:
                    # Lazy formatting for error log
                    LOGGER.error("Missing required IAM policy permissions: %r", e)
                    raise e

                # AWS SSO Admin related exceptions
                except SSO_ADMIN_CLIENT.exceptions.AccessDeniedException as e:
                    # Lazy formatting for error log
                    LOGGER.error("Missing required IAM policy permissions: %r", e)
                    raise e
                except SSO_ADMIN_CLIENT.exceptions.ServiceQuotaExceededException as e:
                    # Lazy formatting for error log
                    LOGGER.error(
                        "Exceeded limit of allowed AWS account assignments, request service quota increase: %r",
                        e,
                    )
                    raise e
                except SSO_ADMIN_CLIENT.exceptions.ResourceNotFoundException as e:
                    # Lazy formatting for error log
                    LOGGER.error(
                        "Invalid TargetID, PrincipalID, or PermissionSetArn: %r", e
                    )
                    raise e

        return wrapper

    return decorator
