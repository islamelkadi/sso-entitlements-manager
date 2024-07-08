# pylint: disable=R0801,W0613
"""
Unit tests to test manifest file ingestion and validate different
YAML configuration files against a JSON schema definition.

Tests:
- test_single_rule_invalid_rules_target_type:
    Validate a single rule with invalid rules target type.
- test_multiple_rules_invalid_rules_target_type:
    Validate multiple rules with invalid rules target type.
- test_single_rule_invalid_rules_access_type:
    Validate a single rule with invalid rules access type.
- test_multiple_rules_invalid_rules_access_type:
    Validate multiple rules with invalid rules access type.
- test_single_rule_missing_permission_set_name:
    Validate a single rule with missing permission set name.
- test_multiple_rules_missing_permission_set_name:
    Validate multiple rules with missing permission set name.
- test_single_rule_missing_principal_name:
    Validate a single rule with missing principal name.
- test_multiple_rules_missing_principal_name:
    Validate multiple rules with missing principal name.
- test_single_rule_invalid_principal_type:
    Validate a single rule with invalid principal type.
- test_multiple_rules_invalid_principal_type:
    Validate multiple rules with invalid principal type.
- test_single_rule_invalid_rule_type:
    Validate a single rule with invalid rule type.
- test_multiple_rule_invalid_rule_type:
    Validate multiple rules with invalid rule type.
"""

import os
import pytest
import jsonschema
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


# Test cases
@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_invalid_rules_target_type(setup_aws_environment) -> None:
    """
    Test case for validating a single rule with invalid rules target type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains invalid rules
    target type according to the manifest schema definition."""
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_invalid_rules_target_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_invalid_rules_target_type(setup_aws_environment) -> None:
    """
    Test case for validating multiple rules with invalid rules target type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains invalid rules
    target type according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD,
        "..",
        "configs",
        "manifests",
        "multiple_rules_invalid_rules_target_type.yaml",
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_invalid_rules_access_type(setup_aws_environment) -> None:
    """
    Test case for validating a single rule with invalid rules access type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains invalid rules
    access type according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_invalid_rules_access_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_invalid_rules_access_type(setup_aws_environment) -> None:
    """
    Test case for validating multiple rules with invalid rules access type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains invalid rules
    access type according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD,
        "..",
        "configs",
        "manifests",
        "multiple_rules_invalid_rules_access_type.yaml",
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_missing_permission_set_name(setup_aws_environment) -> None:
    """
    Test case for validating a single rule with missing permission set name.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains a single rule
    with missing permission set name according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD,
        "..",
        "configs",
        "manifests",
        "single_rule_missing_permission_set_name.yaml",
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_missing_permission_set_name(setup_aws_environment) -> None:
    """
    Test case for validating multiple rules with missing permission set name.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains multiple rules
    with missing permission set name according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD,
        "..",
        "configs",
        "manifests",
        "multiple_rules_missing_permission_set_name.yaml",
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_missing_principal_name(setup_aws_environment) -> None:
    """
    Test case for validating a single rule with missing principal name.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains a single rule
    with missing principal name according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_missing_principal_name.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_missing_principal_name(setup_aws_environment) -> None:
    """
    Test case for validating multiple rules with missing principal name.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains multiple rules
    with missing principal name according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "multiple_rules_missing_principal_name.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_invalid_principal_type(setup_aws_environment) -> None:
    """
    Test case for validating a single rule with invalid principal type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains a single rule
    with invalid principal type according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_missing_principal_name.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_invalid_principal_type(setup_aws_environment) -> None:
    """
    Test case for validating multiple rules with invalid principal type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains multiple rules
    with invalid principal type according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "multiple_rules_invalid_principal_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_invalid_rule_type(setup_aws_environment) -> None:
    """
    Test case for validating a single rule with invalid rule type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains a single rule
    with invalid rule type according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_invalid_rule_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rule_invalid_rule_type(setup_aws_environment) -> None:
    """
    Test case for validating multiple rules with invalid rule type.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    jsonschema.ValidationError: If the YAML file contains multiple rules
    with invalid rule type according to the manifest schema definition.
    """
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "multiple_rules_invalid_rule_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )
