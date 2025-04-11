"""
AWS Identity Center Exceptions Module

This module defines custom exceptions for handling AWS Identity Center (SSO)
specific error conditions. These exceptions help in providing clear and actionable
error messages when dealing with SSO permissions and principals.

Exceptions:
    PermissionSetNotFoundError: Raised when permission sets are missing
    SSOPrincipalNotFoundError: Raised when SSO users/groups are missing

Example:
    try:
        # Attempt to access permission sets
        if not permission_sets:
            raise PermissionSetNotFoundError()
    except PermissionSetNotFoundError as e:
        logger.error("No permission sets available: %s", str(e))

Note:
    These exceptions are typically caught and handled by the AWS exception handler
    decorator in the main Identity Center management flow.
"""

from typing import Literal


class PermissionSetNotFoundError(Exception):
    """
    Raised when no permission sets are available for assignment.

    This exception indicates that the AWS Identity Center instance has no
    permission sets configured, making it impossible to assign access
    to users or groups.

    Example:
        raise PermissionSetNotFoundError(
            "No permission sets found to assign to groups or users principals"
        )
    """

    def __init__(self, message, error_type: Literal["INVALID_PERMISSION_SET_NAME"]):
        self.error_type = error_type
        super().__init__(message)


class SSOPrincipalNotFoundError(Exception):
    """
    Raised when no SSO group(s) or user(s) are found for access assignment.

    This exception indicates that the IAM AWS Identity Center instance has no
    users or groups configured, making it impossible to assign permissions
    to principals. Or it indicates that the AWS IAM Identity Center intance
    has user or group principals, but the target principal is not found.

    Example:
        raise SSOPrincipalNotFoundError(
            "No SSO groups or users principals found to assign access",
            "EMPTY_TENANT"
        )

        raise SSOPrincipalNotFoundError(
            "No SSO group principal found to assign access",
            "INVALID_SSO_GROUP_NAME"
        )

        raise SSOPrincipalNotFoundError(
            "No SSO user principal found to assign access",
            "INVALID_SSO_USER_NAME"
        )
    """

    def __init__(
        self,
        message,
        error_type: Literal[
            "EMPTY_TENANT", "INVALID_SSO_GROUP_NAME", "INVALID_SSO_USER_NAME"
        ],
    ):
        self.error_type = error_type
        super().__init__(message)


class AWSAccountOrOrgNotFoundError(Exception):
    """
    Raised when a target AWS account or OU is not found for permission assignment.

    This exception indicates that the required AWS accounts or OU
    is not available in the AWS Organization configuration, preventing the
    assignment of permissions to users or groups.

    Example:
        raise AWSAccountOrOrgNotFoundError(
            "No AWS account found to assign permissions",
            "INVALID_ACCOUNT_NAME"
        )

        raise AWSAccountOrOrgNotFoundError(
            "No AWS OU found to assign permissions",
            "INVALID_OU_NAME"
        )
    """

    def __init__(
        self, message, error_type: Literal["INVALID_ACCOUNT_NAME", "INVALID_OU_NAME"]
    ):
        self.error_type = error_type
        super().__init__(message)
