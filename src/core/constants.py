from collections import namedtuple

# General constants
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 2.0

# AWS service constants
OU_TARGET_TYPE_LABEL = "OU"
ACCOUNT_TARGET_TYPE_LABEL = "ACCOUNT"
USER_PRINCIPAL_TYPE_LABEL = "USER"
GROUP_PRINCIPAL_TYPE_LABEL = "GROUP"
PERMISSION_SET_TYPE_LABEL = "PERMISSION_SET"
SSO_ENTITLMENTS_APP_NAME = "sso_entitlements_manager"

# Manifest file constants
manifest_file_schema_labels = namedtuple(
    typename="manifest_file_schema_labels",
    field_names=[
        "IGNORE_LABEL",
        "RBAC_RULES_LABEL",
        "TARGET_TYPE_LABEL",
        "TARGET_NAMES_LABEL",
        "PERMISSION_SET_NAME_LABEL",
        "PRINCIPAL_NAME_LABEL",
        "PRINCIPAL_TYPE_LABEL",
        "PRINCIPAL_ID_LABEL"
        "RULE_NUMBER_LABELS"
    ],
    defaults=[
        "ignore",
        "rbac_rules",
        "target_type",
        "target_names",
        "permission_set_name",
        "principal_name",
        "principal_type",
        "principal_id",
        "rule_number"
    ]
)
MANIFEST_RULES_SCHEMA_LABELS = manifest_file_schema_labels()
# # General constants
# retry_configurations = namedtuple(
#     typename="retry_configurations",
#     field_names=["MAX_RETRIES", "RETRY_DELAY_SECONDS"],
#     defaults=[5, 2.0]
# )
# RETRY_CONFIGURATIONS = retry_configurations()

# # AWS service constants
# aws_service_kwarg_names = namedtuple(
#     typename="aws_api_kwarg_names",
#     field_names=[
#         "OU_TARGET_TYPE_LABEL",
#         "ACCOUNT_TARGET_TYPE_LABEL",
#         "USER_PRINCIPAL_TYPE_LABEL",
#         "GROUP_PRINCIPAL_TYPE_LABEL",
#         "PERMISSION_SET_TYPE_LABEL",
#         "SSO_ENTITLMENTS_APP_NAME"
#     ],
#     defaults=[
#         "OU",
#         "ACCOUNT",
#         "USER",
#         "GROUP",
#         "PERMISSION_SET",
#         "sso_entitlements_manager"
#     ]
# )
# AWS_SERVICE_KWARG_NAMES=aws_service_kwarg_names()