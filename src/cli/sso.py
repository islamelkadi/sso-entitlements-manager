"""
AWS SSO Access Management Script.

This script processes an AWS SSO manifest file, maps AWS Organizations entities, and manages 
AWS Identity Center assignments based on RBAC (Role-Based Access Control) rules defined 
in the manifest.

Modules and Classes Used:
-------------------------
- AccessControlFileReader: Reads and validates the AWS SSO manifest file.
- AwsOrganizationsManager: Maps AWS Organizations entities such as OUs and accounts.
- SsoAdminManager: Manages Identity Center assignments and RBAC rules.
"""
import os
import logging
import pathlib
import argparse
from src.core.utils import setup_logging
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.core.access_control_file_reader import AccessControlFileReader
from src.services.aws.aws_organizations_manager import AwsOrganizationsManager
from src.services.aws.aws_identity_centre_manager import IdentityCentreManager

# Constant vars
ROOT_OU_ID = os.getenv("ROOT_OU_ID")
IDENTITY_STORE_ID = os.getenv("IDENTITY_STORE_ID")
IDENTITY_STORE_ARN = os.getenv("IDENTITY_STORE_ARN")
LOGGER = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
CWD = os.path.dirname(os.path.realpath(__file__))
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(
    CWD,
    "..",
    "schemas",
    "manifest_schema_definition.json",
)


def create_sso_assignments(
    manifest_file_path: str,
    auto_approve: bool = False,
    log_level: str = "INFO"
) -> dict:
    """Process AWS SSO access management based on manifest file."""

    # Setup logger
    setup_logging(log_level)

    LOGGER.info("Creating SSO access control assignments")

    manifest_file = AccessControlFileReader(manifest_file_path, MANIFEST_SCHEMA_DEFINITION_FILEPATH)
    aws_organization_manager = AwsOrganizationsManager(ROOT_OU_ID)
    identity_centre_manager = IdentityCentreManager(IDENTITY_STORE_ARN, IDENTITY_STORE_ID)

    # Create account assignments
    identity_centre_manager.is_auto_approved = auto_approve
    identity_centre_manager.manifest_file_rbac_rules = manifest_file.rbac_rules
    identity_centre_manager.account_name_id_map = aws_organization_manager.accounts_name_id_map
    identity_centre_manager.ou_accounts_map = aws_organization_manager.ou_accounts_map
    identity_centre_manager.run_access_control_resolver()

    LOGGER.info("Successfully created SSO access control assignments")

    return {
        "created": identity_centre_manager.assignments_to_create,
        "deleted": identity_centre_manager.assignments_to_delete,
        "invalid": identity_centre_manager.invalid_assignments_report,
    }


if __name__ == "__main__":
    # Initialize CLI arguments parser
    cli_arguments_parser = argparse.ArgumentParser(description="CLI tool to help manage SSO assignments access at scale")

    # Add CLI arguments
    cli_arguments_parser.add_argument(
        "--manifest-filepath",
        required=True,
        type=pathlib.Path,
        help="Local path to the manifest file",
    )
    cli_arguments_parser.add_argument(
        "--auto-approve",
        default=False,
        action="store_true",
        help="Run in auto-approve mode without making any changes",
    )
    cli_arguments_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Log level (default: INFO)",
    )
    cli_arguments = cli_arguments_parser.parse_args()

    # Create SSO assignments
    create_sso_assignments(
        str(cli_arguments.manifest_filepath),
        cli_arguments.auto_approve,
        cli_arguments.log_level,
    )
