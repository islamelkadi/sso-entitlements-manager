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

Key Features:
- Parse SSO manifest file with RBAC rules
- Map AWS Organizations structure
- Create and manage Identity Center access assignments
- Support for auto-approve mode
- Flexible logging configuration

Environment Variables:
- ROOT_OU_ID: Root Organizational Unit ID for AWS Organizations
- IDENTITY_STORE_ID: AWS Identity Center Store ID
- IDENTITY_STORE_ARN: AWS Identity Center Store ARN

Example:
    # Run the script from command line
    python sso_access_management.py --manifest-filepath ./manifest.yaml --auto-approve

Note:
    Requires appropriate AWS IAM permissions for:
    - AWS Organizations listing
    - AWS Identity Center management
    - Reading manifest files
"""

import os
import logging
import pathlib
import argparse
from src.core.utils import setup_logging
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.core.access_control_file_reader import AccessControlFileReader
from src.services.aws.aws_organizations_manager import AwsOrganizationsManager
from src.services.aws.aws_identity_center_manager import IdentityCenterManager

# Constant vars for AWS SSO and Organization configuration
ROOT_OU_ID = os.getenv(
    "ROOT_OU_ID"
)  # Root Organizational Unit ID for traversing AWS Organization
IDENTITY_STORE_ID = os.getenv(
    "IDENTITY_STORE_ID"
)  # Unique identifier for the AWS Identity Center store
IDENTITY_STORE_ARN = os.getenv(
    "IDENTITY_STORE_ARN"
)  # ARN (Amazon Resource Name) for the Identity Center store

# Logging configuration
LOGGER = logging.getLogger(
    SSO_ENTITLMENTS_APP_NAME
)  # Logger for tracking script execution

# Determine the current working directory for relative path resolution
CWD = os.path.dirname(os.path.realpath(__file__))

# Path to the JSON schema used to validate the manifest file
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(
    CWD,
    "..",
    "schemas",
    "manifest_schema_definition.json",
)


def create_sso_assignments(
    manifest_file_path: str, auto_approve: bool = False, log_level: str = "INFO"
) -> dict:
    """
    Process AWS SSO access management based on a manifest file.

    This function reads an SSO manifest, maps AWS Organizations, and creates
    or manages Identity Center access assignments based on RBAC rules.

    Args:
        manifest_file_path (str): Path to the SSO manifest file containing RBAC rules.
        auto_approve (bool, optional): Flag to enable auto-approval mode.
            When True, changes are simulated without actual implementation.
            Defaults to False.
        log_level (str, optional): Logging level for script execution.
            Options include 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
            Defaults to 'INFO'.

    Returns:
        dict: A summary of SSO assignments, including:
            - 'created': Newly created assignments
            - 'deleted': Assignments marked for deletion
            - 'invalid': Assignments that failed validation

    Raises:
        FileNotFoundError: If the manifest file cannot be found.
        ValueError: If the manifest file fails schema validation.
    """

    # Setup logger with specified log level
    setup_logging(log_level)

    LOGGER.info("Creating SSO access control assignments")

    # Read and validate manifest file
    manifest_file = AccessControlFileReader(
        manifest_file_path, MANIFEST_SCHEMA_DEFINITION_FILEPATH
    )

    # Initialize AWS Organizations and Identity Center managers
    aws_organization_manager = AwsOrganizationsManager(ROOT_OU_ID)
    identity_center_manager = IdentityCenterManager(
        IDENTITY_STORE_ARN, IDENTITY_STORE_ID
    )

    # Create account assignments
    identity_center_manager.is_auto_approved = auto_approve
    identity_center_manager.manifest_file_rbac_rules = manifest_file.rbac_rules
    identity_center_manager.account_name_id_map = (
        aws_organization_manager.accounts_name_id_map
    )
    identity_center_manager.ou_accounts_map = aws_organization_manager.ou_accounts_map
    identity_center_manager.run_access_control_resolver()

    LOGGER.info("Successfully created SSO access control assignments")

    return {
        "created": identity_center_manager.assignments_to_create,
        "deleted": identity_center_manager.assignments_to_delete,
        "invalid": identity_center_manager.invalid_assignments_report,
    }


if __name__ == "__main__":
    # Initialize CLI arguments parser
    cli_arguments_parser = argparse.ArgumentParser(
        description="CLI tool to help manage SSO assignments access at scale"
    )

    # Add CLI arguments with detailed help text
    cli_arguments_parser.add_argument(
        "--manifest-filepath",
        required=True,
        type=pathlib.Path,
        help="Local path to the SSO manifest file defining RBAC rules",
    )
    cli_arguments_parser.add_argument(
        "--auto-approve",
        default=False,
        action="store_true",
        help="Run in simulation mode without making actual changes",
    )
    cli_arguments_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity level (default: INFO)",
    )
    cli_arguments = cli_arguments_parser.parse_args()

    # Create SSO assignments
    create_sso_assignments(
        str(cli_arguments.manifest_filepath),
        cli_arguments.auto_approve,
        cli_arguments.log_level,
    )
