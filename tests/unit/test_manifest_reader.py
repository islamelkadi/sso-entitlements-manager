"""
Unit tests for AWS Lambda function using moto to mock S3 interactions.

This module contains helper functions and test cases for the Lambda function.
"""

# Imports
import os
import glob
import pytest
import jsonschema
from src.core.utils import load_file
from src.services.access_manifest_file_reader import AccessManifestReader

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
    CWD, "manifests", "valid_schema", "*.yaml"
)
VALID_MANIFEST_DEFINITION_FILES = [
    os.path.abspath(x) for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)
]

INVALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(
    CWD, "manifests", "invalid_schema", "*.yaml"
)
INVALID_MANIFEST_DEFINITION_FILES = [
    os.path.abspath(x) for x in glob.glob(INVALID_MANIFEST_DEFINITION_FILES_PATH)
]


# Test cases
@pytest.mark.parametrize("manifest_filename", INVALID_MANIFEST_DEFINITION_FILES)
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
        access_manifest_reader = AccessManifestReader()
        setattr(
            access_manifest_reader,
            "schema_definition_filepath",
            MANIFEST_SCHEMA_DEFINITION_FILEPATH,
        )
        setattr(
            access_manifest_reader, "manifest_definition_filepath", manifest_filename
        )
        access_manifest_reader.run_access_manifest_reader()


@pytest.mark.parametrize("manifest_filename", VALID_MANIFEST_DEFINITION_FILES)
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
    manifest_file_via_class = AccessManifestReader()
    setattr(
        manifest_file_via_class,
        "schema_definition_filepath",
        MANIFEST_SCHEMA_DEFINITION_FILEPATH,
    )
    setattr(manifest_file_via_class, "manifest_definition_filepath", manifest_filename)
    manifest_file_via_class.run_access_manifest_reader()

    # Extract excluded lists from the manifest loaded via local
    def get_excluded_names(manifest, target_type):
        return [
            name
            for item in manifest.get("ignore", [])
            if item["target_type"] == target_type
            for name in item.get("target_names", [])
        ]

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

    # Assert
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
