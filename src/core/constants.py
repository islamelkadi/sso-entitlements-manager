"""
Module with constants to use throughout the src/services modules
"""

# General constants for retry mechanisms
MAX_RETRIES = 5  # Maximum number of retry attempts for operations that may fail
RETRY_DELAY_SECONDS = 2.0  # Delay between retry attempts in seconds

# AWS service and identity constants for type labeling
OU_TARGET_TYPE_LABEL = (
    "OU"  # Label representing an Organizational Unit in AWS Organizations
)
ACCOUNT_TARGET_TYPE_LABEL = "ACCOUNT"  # Label representing an AWS account
USER_PRINCIPAL_TYPE_LABEL = "USER"  # Label for identifying individual user principals
GROUP_PRINCIPAL_TYPE_LABEL = "GROUP"  # Label for identifying group principals
PERMISSION_SET_TYPE_LABEL = "PERMISSION_SET"  # Label for AWS SSO permission sets
SSO_ENTITLMENTS_APP_NAME = "sso_entitlements_manager"  # Application name for SSO entitlements logging and identification

# ERROR CODES & Messages
## OU error codes and messages
OU_INVALID_ERROR_CODE = f"INVALID_{OU_TARGET_TYPE_LABEL}_NAME"
OU_INVALID_ERROR_MESSAGE = f"Invalid {OU_TARGET_TYPE_LABEL} - resource not found"

## Account error codes and messages
ACCOUNT_INVALID_ERROR_CODE = f"INVALID_{ACCOUNT_TARGET_TYPE_LABEL}_NAME"
ACCOUNT_INVALID_ERROR_MESSAGE = (
    f"Invalid {ACCOUNT_TARGET_TYPE_LABEL} - resource not found"
)

## SSO Group error codes and messages
SSO_GROUP_INVALID_ERROR_CODE = f"INVALID_SSO_{GROUP_PRINCIPAL_TYPE_LABEL}_NAME"
SSO_GROUP_INVALID_ERROR_MESSAGE = (
    f"Invalid SSO {GROUP_PRINCIPAL_TYPE_LABEL} - resource not found"
)

## SSO User error codes and messages
SSO_USER_INVALID_ERROR_CODE = f"INVALID_SSO_{USER_PRINCIPAL_TYPE_LABEL}_NAME"
SSO_USER_INVALID_ERROR_MESSAGE = (
    f"Invalid SSO {USER_PRINCIPAL_TYPE_LABEL} - resource not found"
)

## Permission Set error codes and messages
PERMISSION_SET_INVALID_ERROR_CODE = f"INVALID_{PERMISSION_SET_TYPE_LABEL}_NAME"
PERMISSION_SET_INVALID_ERROR_MESSAGE = (
    f"Invalid {PERMISSION_SET_TYPE_LABEL} - resource not found"
)
