"""
Multi-Cloud Access Management Tool.

This professional CLI tool manages access assignments across AWS, Azure, and Google Cloud Platform
using infrastructure-as-code patterns with plan/apply workflows. It processes SSO manifest files,
maps cloud organization entities, and manages Identity Center assignments based on RBAC rules.

Modules and Classes Used:
    - AccessControlFileReader: Reads and validates the SSO manifest file.
    - AwsOrganizationsManager: Maps AWS Organizations entities such as OUs and accounts.
    - IdentityCenterManager: Manages Identity Center assignments and RBAC rules.

Key Features:
    - Plan/apply workflow for infrastructure-as-code patterns
    - Parse SSO manifest file with RBAC rules
    - Map cloud organization structures (AWS, Azure, GCP ready)
    - Create and manage Identity Center access assignments
    - Professional multi-cloud access management
    - Flexible logging configuration

Environment Variables:
    - ROOT_OU_ID: Root Organizational Unit ID for AWS Organizations
    - IDENTITY_STORE_ID: AWS Identity Center Store ID
    - IDENTITY_STORE_ARN: AWS Identity Center Store ARN

Examples:
    # Show proposed changes without executing them
    sso-manager plan --manifest-path ./manifest.yaml --log-level INFO
    
    # Execute the proposed changes
    sso-manager apply --manifest-path ./manifest.yaml --log-level INFO

Note:
    Requires appropriate cloud IAM permissions for:
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
from src.core.version import get_version, get_version_info
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


def create_argument_parser():
    """
    Create argument parser with plan/apply subcommands.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser with subcommands
    """
    version_info = get_version_info()
    
    parser = argparse.ArgumentParser(
        description="Multi-Cloud Access Management Tool - Professional infrastructure-as-code access management for AWS, Azure, and Google Cloud Platform",
        prog="sso-manager"
    )
    
    # Add version information
    parser.add_argument(
        '--version',
        action='version',
        version=f"{version_info['name']} {version_info['version']} - {version_info['description']}"
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands for multi-cloud access management',
        required=True
    )
    
    # Plan subcommand
    plan_parser = subparsers.add_parser(
        'plan',
        help='Show proposed access changes without executing them (infrastructure-as-code planning phase)'
    )
    add_common_arguments(plan_parser)
    
    # Apply subcommand
    apply_parser = subparsers.add_parser(
        'apply',
        help='Execute the proposed access changes (infrastructure-as-code apply phase)'
    )
    add_common_arguments(apply_parser)
    
    return parser


def add_common_arguments(parser):
    """
    Add common arguments to subcommand parsers.
    
    Args:
        parser: The subcommand parser to add arguments to
    """
    parser.add_argument(
        '--manifest-path',
        required=True,
        type=pathlib.Path,
        help='Path to the SSO manifest file defining RBAC rules for multi-cloud access management'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging verbosity level for detailed execution tracking (default: INFO)'
    )


def execute_plan(args):
    """
    Execute plan subcommand - shows proposed changes without applying them.
    
    This implements the infrastructure-as-code planning phase, allowing administrators
    to review proposed access changes before execution.
    
    Args:
        args: Parsed command line arguments containing manifest_path and log_level
    """
    create_sso_assignments(
        manifest_file_path=str(args.manifest_path),
        auto_approve=False,
        log_level=args.log_level
    )


def execute_apply(args):
    """
    Execute apply subcommand - applies the proposed changes.
    
    This implements the infrastructure-as-code apply phase, executing the
    access changes defined in the manifest file.
    
    Args:
        args: Parsed command line arguments containing manifest_path and log_level
    """
    create_sso_assignments(
        manifest_file_path=str(args.manifest_path),
        auto_approve=True,
        log_level=args.log_level
    )


def main():
    """
    Main CLI entry point with subcommand routing.
    
    Implements professional multi-cloud access management with plan/apply workflow
    supporting AWS, Azure, and Google Cloud Platform infrastructure-as-code patterns.
    """
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if args.command == 'plan':
        execute_plan(args)
    elif args.command == 'apply':
        execute_apply(args)


if __name__ == "__main__":
    main()
