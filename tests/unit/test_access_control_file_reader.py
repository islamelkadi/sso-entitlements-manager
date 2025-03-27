"""
Unit Tests for AWS Lambda Function Manifest Schema Validation

This module contains unit tests for validating manifest file schemas using 
the AccessControlFileReader. It provides test cases for both valid and 
invalid manifest file schemas, ensuring proper validation of configuration files.
"""

# Imports
import os
import glob
import pytest
import jsonschema
from src.core.utils import load_file
from src.core.access_control_file_reader import AccessControlFileReader

# Constants
CWD = os.path.dirname(os.path.realpath(__file__))
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(
    CWD,
    "..",
    "..",
    "src",
    "schemas",
    "manifest_schema_definition.json",
)

# Dynamic generation of filenames
VALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(
    CWD, "..", "manifests", "valid_schema", "*.yaml"
)
VALID_MANIFEST_DEFINITION_FILES = [
    os.path.abspath(x) for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)
]

INVALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(
    CWD, "..", "manifests", "invalid_schema", "*.yaml"
)
INVALID_MANIFEST_DEFINITION_FILES = [
    os.path.abspath(x) for x in glob.glob(INVALID_MANIFEST_DEFINITION_FILES_PATH)
]


@pytest.mark.parametrize("manifest_filename", INVALID_MANIFEST_DEFINITION_FILES)
def test_rules_invalid_manifest_schema(manifest_filename: str) -> None:
    """
    Validate that manifest files with invalid schema definitions raise a ValidationError.

    This test ensures that AccessControlFileReader properly validates manifest file schemas
    and raises a jsonschema.ValidationError for configurations that do not meet the
    defined schema requirements.

    Args:
        manifest_filename (str): Absolute path to the manifest file to be validated.

    Asserts:
        - A jsonschema.ValidationError is raised when attempting to create an
          AccessControlFileReader with an invalid manifest file.

    Raises:
        jsonschema.ValidationError: If the manifest file does not conform to the
            defined schema requirements.

    Note:
        This test is parameterized to run against multiple invalid manifest files.
    """
    # Assert that an invalid manifest file raises a ValidationError
    with pytest.raises(jsonschema.ValidationError):
        # Attempt to create AccessControlFileReader with an invalid manifest
        AccessControlFileReader(manifest_filename, MANIFEST_SCHEMA_DEFINITION_FILEPATH)


@pytest.mark.parametrize("manifest_filename", VALID_MANIFEST_DEFINITION_FILES)
def test_rules_valid_manifest_schema(manifest_filename: str) -> None:
    """
    Validate the correct parsing of manifest files with valid schema definitions.

    This test verifies that:
        1. The manifest file can be loaded successfully using both local loading
        and AccessControlFileReader methods.
        2. Excluded lists (OU, Account, SSO User, SSO Group, Permission Set)
        are correctly extracted and match between different loading methods.

    Args:
        manifest_filename (str): Absolute path to the manifest file to be tested.

    Asserts:
        - Excluded Organizational Unit (OU) names match between
          local file loading method and AccessControlFileReader class method.
        - Excluded Account names match between local file loading
          method and AccessControlFileReader class method.
        - Excluded SSO User names match between local file loading
          method and AccessControlFileReader class method.
        - Excluded SSO Group names match between local file loading
          method and AccessControlFileReader class method.
        - Excluded Permission Set names match between local file loading
          method and AccessControlFileReader class method.

    Note:
        This test is parameterized to run against multiple valid manifest files.
    """
    # Load manifest file via local method and AccessControlFileReader
    manifest_file_via_local = load_file(manifest_filename)
    manifest_file_via_class = AccessControlFileReader(
        manifest_filename, MANIFEST_SCHEMA_DEFINITION_FILEPATH
    )

    # Helper function to extract excluded names from a manifest
    def get_excluded_names(manifest, target_type):
        """
        Extract excluded names for a specific target type from a manifest.

        Args:
            manifest (dict): The manifest dictionary to extract names from.
            target_type (str): The type of target to filter (e.g., 'OU', 'ACCOUNT').

        Returns:
            list: A list of excluded names for the specified target type.
        """
        return [
            name
            for item in manifest.get("ignore", [])
            if item["target_type"] == target_type
            for name in item.get("target_names", [])
        ]

    # Extract excluded names using the helper function
    excluded_ou_names_local = get_excluded_names(manifest_file_via_local, "OU")
    excluded_account_names_local = get_excluded_names(
        manifest_file_via_local, "ACCOUNT"
    )
    excluded_sso_user_names_local = get_excluded_names(manifest_file_via_local, "USER")
    excluded_sso_group_names_local = get_excluded_names(
        manifest_file_via_local, "GROUP"
    )
    excluded_permission_set_names_local = get_excluded_names(
        manifest_file_via_local, "PERMISSION_SET"
    )

    # Assert that excluded names match between local and class methods
    assert (
        manifest_file_via_class.excluded_ou_names == excluded_ou_names_local
    ), "excluded_ou_names do not match"
    assert (
        manifest_file_via_class.excluded_account_names == excluded_account_names_local
    ), "excluded_account_names do not match"
    assert (
        manifest_file_via_class.excluded_sso_user_names == excluded_sso_user_names_local
    ), "excluded_sso_user_names do not match"
    assert (
        manifest_file_via_class.excluded_sso_group_names
        == excluded_sso_group_names_local
    ), "excluded_sso_group_names do not match"
    assert (
        manifest_file_via_class.excluded_permission_set_names
        == excluded_permission_set_names_local
    ), "excluded_permission_set_names do not match"
