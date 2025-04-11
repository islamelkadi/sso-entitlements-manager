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
