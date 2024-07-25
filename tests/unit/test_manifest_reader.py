"""
Unit tests for AWS Lambda function using moto to mock S3 interactions.

This module contains helper functions and test cases for the Lambda function.
"""

# Imports
import os
import glob
import pytest
import jsonschema
from app.lib.utils import load_file
from app.lib.access_manifest_reader import AccessManifestReader

# Constants
CWD = os.path.dirname(os.path.realpath(__file__))
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(
    CWD,
    "..",
    "..",
    "src",
    "app",
    "schemas",
    "manifest_schema_definition.json",
)

# Helper function to get all filenames in a directory
def get_filenames_from_directory(directory: str, extension: str) -> list:
    """
    Retrieve all filenames with a specific extension from a given directory.

    Args:
    ----
    directory: str
        Path to the directory.
    extension: str
        File extension to match (e.g., '.yaml').

    Returns:
    -------
    list of str: List of file paths.
    """
    pattern = os.path.join(directory, f"*{extension}")
    return glob.glob(pattern)

# Dynamic generation of filenames
valid_manifest_files = get_filenames_from_directory(
    os.path.join(CWD, "..", "configs", "manifests", "valid_schema"), ".yaml"
)

invalid_manifest_files = get_filenames_from_directory(
    os.path.join(CWD, "..", "configs", "manifests", "invalid_schema"), ".yaml"
)

# Test cases
@pytest.mark.parametrize("manifest_filename", invalid_manifest_files)
def test_rules_invalid_manifest_schema(manifest_filename: str) -> None:
    """
    Test to validate manifest files with invalid schema definitions.

    This test checks if manifest files with various invalid schema
    configurations raise a jsonschema.ValidationError when processed
    by the AccessManifestReader.

    Parameters:
    ----------
        manifest_filename (str): Path to the manifest file to validate.

    Asserts:
    -------
        jsonschema.ValidationError: If the manifest file schema is invalid.
    """
    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AccessManifestReader(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_filename)

@pytest.mark.parametrize("manifest_filename", valid_manifest_files)
def test_rules_valid_manifest_schema(manifest_filename: str) -> None:
    """
    Test the lambda_handler function with a mocked S3 environment.

    Parameters:
    ----------
    manifest_filename : str
        The filename of the manifest to be tested.
    """
    # Act
    manifest_file_via_local = load_file(manifest_filename)
    manifest_file_via_class = AccessManifestReader(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_filename)

    # Extract excluded lists from the manifest loaded via local
    def get_excluded_names(manifest, target_type):
        return [
            name
            for item in manifest.get("ignore", [])
            if item["target_type"] == target_type
            for name in item.get("target_names", [])
        ]

    excluded_ou_names_local = get_excluded_names(manifest_file_via_local, "OU")
    excluded_account_names_local = get_excluded_names(manifest_file_via_local, "ACCOUNT")
    excluded_sso_user_names_local = get_excluded_names(manifest_file_via_local, "USER")
    excluded_sso_group_names_local = get_excluded_names(manifest_file_via_local, "GROUP")
    excluded_permission_set_names_local = get_excluded_names(manifest_file_via_local, "PERMISSION_SET")

    # Assert
    assert manifest_file_via_class.excluded_ou_names == excluded_ou_names_local, "excluded_ou_names do not match"
    assert manifest_file_via_class.excluded_account_names == excluded_account_names_local, "excluded_account_names do not match"
    assert manifest_file_via_class.excluded_sso_user_names == excluded_sso_user_names_local, "excluded_sso_user_names do not match"
    assert manifest_file_via_class.excluded_sso_group_names == excluded_sso_group_names_local, "excluded_sso_group_names do not match"
    assert manifest_file_via_class.excluded_permission_set_names == excluded_permission_set_names_local, "excluded_permission_set_names do not match"
