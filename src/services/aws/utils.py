import logging
import functools
from typing import Callable, Any

import boto3
from src.core.constants import SSO_ENTITLMENTS_APP_NAME

logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
sso_admin_client = boto3.client("sso-admin")
aws_organization_client = boto3.client("organizations")


def handle_aws_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle AWS Organizations API exceptions.
    
    Parameters:
    -----------
    func: Callable
        The function to wrap
        
    Returns:
    --------
    Callable
        The wrapped function
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        try:
            return func(self, *args, **kwargs)

        # AWS Organizations related exceptions
        except aws_organization_client.exceptions.ParentNotFoundException as e:
            logger.error(f"Invalid parent OU name: {e}")
            raise e
        except aws_organization_client.exceptions.AccessDeniedException as e:
            logger.error(f"Missing required IAM policy permissions: {e}")
            raise e
        except aws_organization_client.exceptions.ServiceException as e:
            logger.error(f"Unexpected service internal error: {e}")
            raise e

        # AWS SSO Admin related exceptions
        except sso_admin_client.exceptions.AccessDeniedException as e:
            logger.error(f"Missing required IAM policy permissions: {e}")
            raise e
        except sso_admin_client.exceptions.ServiceQuotaExceededException as e:
            logger.error(f"Exceeded limit of allowed AWS account assignments, request service quota increase: {e}")
            raise e
        except sso_admin_client.exceptions.ResourceNotFoundException as e:
            logger.error(f"Invalid TargetID, PrincipalID, or PermissionSetArn: {e}")
            raise e
        except sso_admin_client.exceptions.InternalServerException as e:
            logger.error(f"Unexpected service internal server error: {e}")
            raise e
    return wrapper
