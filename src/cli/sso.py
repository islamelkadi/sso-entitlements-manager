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
"""

import os
from pathlib import Path
import typer
from src.services.access_manifest_file_reader import AccessManifestReader
from src.services.aws_organizations_mapper import AwsOrganizationsMapper
from src.services.aws_identity_center_manager import AwsIdentityCenterManager

# Initialize Typer app
app = typer.Typer(help="AWS SSO Access Management CLI", add_completion=False)

# Globals
MANIFEST_FILE_S3_LOCATION = os.getenv("MANIFEST_FILE_S3_LOCATION")


@app.callback(invoke_without_command=True)
def main(
    manifest_file_path: Path = typer.Option(..., "--manifest", "-m", help="Local path to the manifest file", exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    manifest_schema_path: Path = typer.Option(..., "--schema", "-s", help="Local path to the manifest schema file", exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Run in dry-run mode without making any changes", is_flag=True),
) -> dict:
    """Process AWS SSO access management based on manifest file."""

    # Process manifest file
    manifest_file = AccessManifestReader()
    manifest_file.manifest_definition_filepath = manifest_file_path
    manifest_file.schema_definition_filepath = manifest_schema_path
    manifest_file.run_access_manifest_reader()

    # Initialize OU & Accounts map
    aws_org = AwsOrganizationsMapper()
    aws_org.exclude_ou_name_list = manifest_file.excluded_ou_names
    aws_org.exclude_account_name_list = manifest_file.excluded_account_names
    aws_org.run_ous_accounts_mapper()

    # Create account assignments
    identity_center_manager = AwsIdentityCenterManager()
    identity_center_manager.is_dry_run = dry_run
    identity_center_manager.rbac_rules = manifest_file.rbac_rules
    identity_center_manager.exclude_sso_users = manifest_file.excluded_sso_user_names
    identity_center_manager.exclude_sso_groups = manifest_file.excluded_sso_group_names
    identity_center_manager.exclude_permission_sets = manifest_file.excluded_permission_set_names
    identity_center_manager.account_name_id_map = aws_org.account_name_id_map
    identity_center_manager.ou_accounts_map = aws_org.ou_accounts_map
    identity_center_manager.run_access_control_resolver()

    results = {
        "created": identity_center_manager.assignments_to_create,
        "deleted": identity_center_manager.assignments_to_delete,
        "invalid": identity_center_manager.invalid_manifest_rules_report,
    }

    return results


if __name__ == "__main__":
    app()
