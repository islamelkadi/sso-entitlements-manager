import logging
import functools
from typing import Callable, Any
from src.core.constants import SSO_ENTITLMENTS_APP_NAME

logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)

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
        except self._organizations_client.exceptions.ParentNotFoundException as e:
            logger.error(f"Invalid parent OU name: {e}")
            raise e
        except self._organizations_client.exceptions.AccessDeniedException as e:
            logger.error(f"Missing required IAM policy permissions: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise e
    return wrapper
