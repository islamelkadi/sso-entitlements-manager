"""
Unit tests to test writing regex rules from DDB
"""
import os
import pytest
import jsonschema
from app.lib.aws_sso_resolver import AwsResolver

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
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_invalid_rules_target_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_invalid_rules_target_type(setup_aws_environment) -> None:
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
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_invalid_rules_access_type(setup_aws_environment) -> None:
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_invalid_rules_access_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_invalid_rules_access_type(setup_aws_environment) -> None:
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
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_missing_permission_set_name(setup_aws_environment) -> None:
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
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_missing_permission_set_name(setup_aws_environment) -> None:
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
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_missing_principal_name(setup_aws_environment) -> None:
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_missing_principal_name.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_missing_principal_name(setup_aws_environment) -> None:
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "multiple_rules_missing_principal_name.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_invalid_principal_type(setup_aws_environment) -> None:
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_missing_principal_name.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_invalid_principal_type(setup_aws_environment) -> None:
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "multiple_rules_invalid_principal_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_single_rule_invalid_rule_type(setup_aws_environment) -> None:
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "single_rule_invalid_rule_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rule_invalid_rule_type(setup_aws_environment) -> None:
    # Arrange
    manifest_definition_filepath = os.path.join(
        CWD, "..", "configs", "manifests", "multiple_rules_invalid_rule_type.yaml"
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)
