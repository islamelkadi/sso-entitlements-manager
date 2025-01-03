"""
AWS SSO Access Management Script.

This script processes an AWS SSO manifest file, maps AWS Organizations entities, and manages 
AWS Identity Center assignments based on RBAC (Role-Based Access Control) rules defined 
in the manifest.

Modules and Classes Used:
-------------------------
- AccessManifestReader: Reads and validates the AWS SSO manifest file.
- AwsOrganizationsMapper: Maps AWS Organizations entities such as OUs and accounts.
- AwsIdentityCenterManager: Manages Identity Center assignments and RBAC rules.

Global Variables:
-----------------
MANIFEST_FILE_S3_LOCATION : str
    S3 location of the manifest file, retrieved from the environment variable.

Functions:
----------
main(args):
    Processes the manifest file, maps AWS Organizations entities, and resolves AWS Identity Center 
    access control assignments.

    Args:
    -----
    args : argparse.Namespace
        Command-line arguments including dry-run mode, manifest schema filepath, 
        and local manifest file path.

    Returns:
    --------
    dict:
        A dictionary containing:
            - created: List of assignments created.
            - deleted: List of assignments deleted.
            - invalid: Report of invalid RBAC rules in the manifest.

Command-Line Arguments:
-----------------------
--dry-run : bool
    Run the script in dry-run mode without making actual changes.

--manifest-schema-definition-filepath : str
    Path to the schema definition file for validating the manifest.

--manifest-file-local-path : str
    Path to the local manifest file.

Usage Example:
--------------
python script.py --dry-run --manifest-file-local-path ./manifests/sample_manifest.json
"""

import os
import argparse
from src.services.access_manifest_file_reader import AccessManifestReader
from src.services.aws_organizations_mapper import AwsOrganizationsMapper
from src.services.aws_identity_center_manager import AwsIdentityCenterManager

# Globals
MANIFEST_FILE_S3_LOCATION = os.getenv("MANIFEST_FILE_S3_LOCATION")


def main(arguments):
    """
    Main function to process AWS SSO manifest, map AWS Organizations entities,
    and resolve Identity Center assignments.

    Args:
    -----
    arguments : argparse.Namespace
        Command-line arguments including dry-run mode, schema definition file path,
        and manifest file path.

    Returns:
    --------
    dict:
        A dictionary containing:
            - created: List of assignments created.
            - deleted: List of assignments deleted.
            - invalid: Report of invalid RBAC rules in the manifest.
    """
    # Ensure arguments is Namespace
    if isinstance(arguments, dict):
        arguments = argparse.Namespace(**arguments)
        print(arguments)

    # # Process manifest file
    # manifest_file = AccessManifestReader()
    # manifest_file.schema_definition_filepath = arguments.manifest_schema_definition_filepath
    # manifest_file.manifest_definition_filepath = arguments.manifest_file_local_path
    # manifest_file.run_access_manifest_reader()

    # # Initialize OU & Accounts map
    # aws_org = AwsOrganizationsMapper()
    # aws_org.exclude_ou_name_list = manifest_file.excluded_ou_names
    # aws_org.exclude_account_name_list = manifest_file.excluded_account_names
    # aws_org.run_ous_accounts_mapper()

    # # Create account assignments
    # identity_center_manager = AwsIdentityCenterManager()
    # identity_center_manager.is_dry_run = arguments.dry_run
    # identity_center_manager.rbac_rules = manifest_file.rbac_rules
    # identity_center_manager.exclude_sso_users = manifest_file.excluded_sso_user_names
    # identity_center_manager.exclude_sso_groups = manifest_file.excluded_sso_group_names
    # identity_center_manager.exclude_permission_sets = manifest_file.excluded_permission_set_names
    # identity_center_manager.account_name_id_map = aws_org.account_name_id_map
    # identity_center_manager.ou_accounts_map = aws_org.ou_accounts_map
    # identity_center_manager.run_access_control_resolver()

    # return {
    #     "created": identity_center_manager.assignments_to_create,
    #     "deleted": identity_center_manager.assignments_to_delete,
    #     "invalid": identity_center_manager.invalid_manifest_rules_report,
    # }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", default=False, help="Run in dry-run mode"
    )
    parser.add_argument(
        "--manifest-schema-definition-filepath",
        default="./schemas/manifest_schema_definition.json",
        help="Path to the manifest schema definition file",
    )
    parser.add_argument(
        "--manifest-file-local-path",
        required=True,
        help="Path to the local manifest file",
    )
    args = parser.parse_args()
    main(args)
