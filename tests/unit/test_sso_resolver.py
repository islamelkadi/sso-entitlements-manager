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
- test_multiple_rules_invalid_rule_type:
    Validate multiple rules with invalid rule type.
"""

import os
import pytest
import jsonschema
from app.lib.utils import load_file, convert_list_to_dict
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

def flatten_accounts(units):
    def _flatten(units):
        for unit in units:
            if unit["type"] == "ACCOUNT":
                yield unit
            if "children" in unit:
                yield from _flatten(unit["children"])
    return list(_flatten(units))

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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "single_rule_invalid_rules_target_type.yaml",
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
        "invalid",
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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "single_rule_invalid_rules_access_type.yaml",
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
        "invalid",
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
        "invalid",
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
        "invalid",
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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "single_rule_missing_principal_name.yaml",
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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "multiple_rules_missing_principal_name.yaml",
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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "single_rule_missing_principal_name.yaml",
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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "multiple_rules_invalid_principal_type.yaml",
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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "single_rule_invalid_rule_type.yaml",
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_invalid_rule_type(setup_aws_environment) -> None:
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
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid",
        "multiple_rules_invalid_rule_type.yaml",
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_multiple_rules_valid(setup_aws_environment) -> None:
    ou_map = convert_list_to_dict(setup_aws_environment["aws_organization_definitions"], "name")
    sso_user_map = convert_list_to_dict(setup_aws_environment["aws_sso_user_definitions"], "username")
    sso_group_map = convert_list_to_dict(setup_aws_environment["aws_sso_group_definitions"], "name")
    permission_set_map = convert_list_to_dict(setup_aws_environment["aws_permission_set_definitions"], "name")
    manifest_definition_filepath = os.path.join(
        CWD,
        "..",
        "configs",
        "manifests",
        "valid",
        "multiple_rules_valid.yaml",
    )
    manifest_file = load_file(manifest_definition_filepath)

    aws_access_resolver = AwsAccessResolver(
        MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
    )

    # Extract ignore section
    ignore_accounts = set()
    for ignore_rule in manifest_file.get("ignore", []):
        if ignore_rule["target_type"] == "ACCOUNT":
            ignore_accounts.update(ignore_rule["target_names"])
        elif ignore_rule["target_type"] == "OU":
            for ou_name in ignore_rule["target_names"]:
                if ou_name in ou_map:
                    ignore_accounts.update(
                        account["name"] for account in ou_map[ou_name]["children"]
                        if account["type"] == "ACCOUNT"
                    )

    # Extract rules section and validate
    unique_combinations = set()
    for rule in manifest_file.get("rules", []):
        if rule["principal_type"] == "USER" and rule["principal_name"] not in sso_user_map:
            continue
        if rule["principal_type"] == "GROUP" and rule["principal_name"] not in sso_group_map:
            continue
        if rule["permission_set_name"] not in permission_set_map:
            continue

        target_names = rule["target_names"]
        if rule["target_type"] == "ACCOUNT":
            valid_targets = [name for name in target_names if name not in ignore_accounts]
        elif rule["target_type"] == "OU":
            valid_targets = [
                account["name"] for ou_name in target_names if ou_name in ou_map
                for account in ou_map[ou_name]["children"] if account["name"] not in ignore_accounts
            ]

        unique_combinations.update((rule["principal_name"], rule["permission_set_name"], target) for target in valid_targets)

    # Assert the length of unique combinations matches the successful RBAC assignments
    assert len(unique_combinations) == len(aws_access_resolver.successful_rbac_assignments)