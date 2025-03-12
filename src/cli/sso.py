"""
AWS SSO Access Management Script.

This script processes an AWS SSO manifest file, maps AWS Organizations entities, and manages 
AWS Identity Center assignments based on RBAC (Role-Based Access Control) rules defined 
in the manifest.

Modules and Classes Used:
-------------------------
- AccessControlFileReader: Reads and validates the AWS SSO manifest file.
- OrganizationsMapper: Maps AWS Organizations entities such as OUs and accounts.
- SsoAdminManager: Manages Identity Center assignments and RBAC rules.
"""
import os
import logging
import pathlib
import argparse
from src.core.utils import setup_logging
from src.core.access_control_file_reader import AccessControlFileReader
from src.services.aws.organizations_mapper import OrganizationsMapper
from src.services.aws.access_control_resolver import SsoAdminManager
from src.core.constants import SSO_ENTITLMENTS_APP_NAME

# Globals vars
CWD = os.path.dirname(os.path.realpath(__file__))
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(
    CWD,
    "..",
    "schemas",
    "manifest_schema_definition.json",
)

# Setup non-root logger
logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)


def create_sso_assignments(
    manifest_file_path: str,
    auto_approve: bool = False,
    log_level: str = "INFO"
) -> dict:
    """Process AWS SSO access management based on manifest file."""

    # Setup logger
    setup_logging(log_level)

    logger.info("Creating SSO access control assignments")

    # Process manifest file
    manifest_file = AccessControlFileReader(manifest_file_path, MANIFEST_SCHEMA_DEFINITION_FILEPATH)

    # Initialize OU & Accounts map
    aws_org = OrganizationsMapper()
    aws_org.run_ous_accounts_mapper()

    # Create account assignments
    identity_center_manager = SsoAdminManager()
    identity_center_manager.is_auto_approved = auto_approve
    identity_center_manager.rbac_rules = manifest_file.rbac_rules
    identity_center_manager.exclude_sso_users = manifest_file.excluded_sso_user_names
    identity_center_manager.exclude_sso_groups = manifest_file.excluded_sso_group_names
    identity_center_manager.exclude_permission_sets = manifest_file.excluded_permission_set_names
    identity_center_manager.account_name_id_map = aws_org.account_name_id_map
    identity_center_manager.ou_accounts_map = aws_org.ou_accounts_map
    identity_center_manager.run_access_control_resolver()

    logger.info("Successfully created SSO access control assignments")

    return {
        "created": identity_center_manager.assignments_to_create,
        "deleted": identity_center_manager.assignments_to_delete,
        "invalid": identity_center_manager.invalid_manifest_rules_report,
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
