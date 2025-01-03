"""
Constants for AWS SSO manifest processing.

This module defines string constants used as labels for various target and principal types 
in AWS SSO manifests. These constants are primarily utilized in manifest processing, 
validation, and exclusion list generation.

Constants:
----------
OU_TARGET_TYPE_LABEL : str
    Represents the Organizational Unit (OU) target type in AWS SSO manifests.

ACCOUNT_TARGET_TYPE_LABEL : str
    Represents the Account target type in AWS SSO manifests.

USER_PRINCIPAL_TYPE_LABEL : str
    Represents the User principal type in AWS SSO manifests.

GROUP_PRINCIPAL_TYPE_LABEL : str
    Represents the Group principal type in AWS SSO manifests.

PERMISSION_SET_TYPE_LABEL : str
    Represents the Permission Set type in AWS SSO manifests.
"""

OU_TARGET_TYPE_LABEL = "OU"
ACCOUNT_TARGET_TYPE_LABEL = "ACCOUNT"
USER_PRINCIPAL_TYPE_LABEL = "USER"
GROUP_PRINCIPAL_TYPE_LABEL = "GROUP"
PERMISSION_SET_TYPE_LABEL = "PERMISSION_SET"
