"""
Regex based rules engine for processing regex input for the
purpose of assiging permission sets.
"""
import os
from http import HTTPStatus

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent, event_source

from .lib.utils import download_file_from_s3
from .lib.ous_accounts_mapper import AwsOrganizations
from .lib.identity_center_mapper import AwsIdentityCenter
from .lib.access_control_resolver import AwsAccessResolver
from .lib.access_manifest_reader import AccessManifestReader

# Globals
ROOT_OU_ID = os.getenv("ROOT_OU_ID")
IS_DRY_RUN = os.getenv("DRY_RUN", True)
IDENTITY_STORE_ID = os.getenv("IDENTITY_STORE_ID")
IDENTITY_STORE_ARN = os.getenv("IDENTITY_STORE_ARN")
MANIFEST_FILE_S3_LOCATION = os.getenv("MANIFEST_FILE_S3_LOCATION")
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "schemas", "manifest_schema_definition.json")

# AWS Lambda powertool objects & class instances
TRACER = Tracer()
LOGGER = Logger()


# Lambda handler
@TRACER.capture_lambda_handler
@event_source(data_class=EventBridgeEvent)  # pylint: disable=E1120
@LOGGER.inject_lambda_context(log_event=True, correlation_id_path=correlation_paths.EVENT_BRIDGE)
def lambda_handler(event: EventBridgeEvent, context: LambdaContext):  # pylint: disable=W0613
    """
    Function to create or retrieve regex rules for SSO permission
    set assignments

    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
    response: dict
        - body: contains stringified response of lambda function
        - statusCode: contains HTTP status code
    """

    # Download manifest file
    manifest_file_local_path = download_file_from_s3(MANIFEST_FILE_S3_LOCATION)
    manifest_file = AccessManifestReader(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_file_local_path)

    # Initialize OU & Accounts map
    aws_org = AwsOrganizations(ROOT_OU_ID)
    setattr(aws_org, "exclude_ou_name_list", manifest_file.excluded_ou_names)
    setattr(aws_org, "exclude_account_name_list", manifest_file.excluded_account_names)
    aws_org.run_ous_accounts_mapper()

    # Initialize SSO Groups, Users, & Permission sets map
    aws_idc = AwsIdentityCenter(IDENTITY_STORE_ID, IDENTITY_STORE_ARN)
    setattr(aws_idc, "exclude_sso_users", manifest_file.excluded_sso_user_names)
    setattr(aws_idc, "exclude_sso_groups", manifest_file.excluded_sso_group_names)
    setattr(aws_idc, "exclude_permission_sets", manifest_file.excluded_permission_set_names)
    aws_idc.run_identity_center_mapper()

    # Create account assignments
    aws_access_resolver = AwsAccessResolver(IDENTITY_STORE_ARN)
    setattr(aws_access_resolver, "dry_run", IS_DRY_RUN)
    setattr(aws_access_resolver, "rbac_rules", manifest_file.rbac_rules)
    setattr(aws_access_resolver, "sso_users", aws_idc.sso_users)
    setattr(aws_access_resolver, "sso_groups", aws_idc.sso_groups)
    setattr(aws_access_resolver, "permission_sets", aws_idc.permission_sets)
    setattr(aws_access_resolver, "account_name_id_map", aws_org.account_name_id_map)
    setattr(aws_access_resolver, "ou_accounts_map", aws_org.ou_accounts_map)
    aws_access_resolver.run_access_control_resolver()

    return Response(
        status_code=HTTPStatus.OK.value,
        content_type=content_types.APPLICATION_JSON,
        body={
            "created": aws_access_resolver.assignments_to_create,
            "deleted": aws_access_resolver.assignments_to_delete,
            "invalid": aws_access_resolver.invalid_manifest_rules_report,
        },
    )
