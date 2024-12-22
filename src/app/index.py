"""
Regex based rules engine for processing regex input for the
purpose of assiging permission sets.
"""
import os
import sys

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent, event_source

sys.path.append(os.path.join(os.path.dirname(__file__)))

from lib.utils import download_file_from_s3
from lib.access_manifest_file_reader import AccessManifestReader
from lib.aws_organizations_mapper import AwsOrganizationsMapper
from lib.aws_identity_center_manager import AwsIdentityCenterManager

# Globals
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
    aws_org = AwsOrganizationsMapper()
    setattr(aws_org, "exclude_ou_name_list", manifest_file.excluded_ou_names)
    setattr(aws_org, "exclude_account_name_list", manifest_file.excluded_account_names)
    aws_org.run_ous_accounts_mapper()

    # Create account assignments
    identity_center_manager = AwsIdentityCenterManager()
    setattr(identity_center_manager, "rbac_rules", manifest_file.rbac_rules)
    setattr(identity_center_manager, "exclude_sso_users", manifest_file.excluded_sso_user_names)
    setattr(identity_center_manager, "exclude_sso_groups", manifest_file.excluded_sso_group_names)
    setattr(identity_center_manager, "exclude_permission_sets", manifest_file.excluded_permission_set_names)
    setattr(identity_center_manager, "account_name_id_map", aws_org.account_name_id_map)
    setattr(identity_center_manager, "ou_accounts_map", aws_org.ou_accounts_map)
    identity_center_manager.run_access_control_resolver()

    LOGGER.info("Lambda execution complete")
    LOGGER.info("Created %s assignments", len(identity_center_manager.assignments_to_create))
    LOGGER.info("Deleted %s assignments", len(identity_center_manager.assignments_to_delete))
    LOGGER.info("Invalid %s assignments", len(identity_center_manager.invalid_manifest_rules_report))

    return {
        "created": identity_center_manager.assignments_to_create,
        "deleted": identity_center_manager.assignments_to_delete,
        "invalid": identity_center_manager.invalid_manifest_rules_report,
    }