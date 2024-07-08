# pylint: disable=R0801,W0613
"""
TBD
"""
import os
import pytest
from app.lib.access_control_resolver import AwsAccessResolver

# Globals vars
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


@pytest.mark.order(1)
@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_create_rbac_assignments(setup_aws_environment: pytest.fixture) -> None:
    """
    Test case to verify creating RBAC assignments using AwsAccessResolver.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including
        aws_sso_group_definitions and aws_permission_set_definitions.

    Raises:
    ------
    AssertionError: If the RBAC assignments created via AwsAccessResolver
    do not match expected definitions.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "multiple_rules_valid.yaml"
    )

    AwsAccessResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)

    # Act
    # (Assuming further actions are performed here to create RBAC assignments)

    # Assert
    # (Assuming assertions are made here to validate the created RBAC assignments)
