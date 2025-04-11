"""
AWS Identity Center Exceptions Module

This module defines custom exceptions for handling AWS Identity Center (SSO)
specific error conditions. These exceptions help in providing clear and actionable
error messages when dealing with SSO permissions and principals.

Exceptions:
    NoPermissionSetsFoundError: Raised when permission sets are missing
    NoSSOPrincipalsFoundError: Raised when SSO users/groups are missing

Example:
    try:
        # Attempt to access permission sets
        if not permission_sets:
            raise NoPermissionSetsFoundError()
    except NoPermissionSetsFoundError as e:
        logger.error("No permission sets available: %s", str(e))

Note:
    These exceptions are typically caught and handled by the AWS exception handler
    decorator in the main Identity Center management flow.
"""


class NoPermissionSetsFoundError(Exception):
    """
    Raised when no permission sets are available for assignment.

    This exception indicates that the AWS Identity Center instance has no
    permission sets configured, making it impossible to assign access
    to users or groups.

    Example:
        raise NoPermissionSetsFoundError(
            "No permission sets found to assign to groups or users principals"
        )
    """


class NoSSOPrincipalsFoundError(Exception):
    """
    Raised when no SSO groups or users are found for access assignment.

    This exception indicates that the AWS Identity Center instance has no
    users or groups configured, making it impossible to assign permissions
    to principals.

    Example:
        raise NoSSOPrincipalsFoundError(
            "No SSO groups or users principals found to assign access"
        )
    """
