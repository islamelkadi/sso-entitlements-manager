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
import itertools
from typing import Dict, List, Set, Tuple

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

# Type Definitions
AwsEnvironment = Dict[str, List[Dict[str, str]]]
OuMap = Dict[str, Dict[str, List[Dict[str, str]]]]
SsoMap = Dict[str, Dict[str, str]]
ManifestFile = Dict[str, List[Dict[str, List[str]]]]
UniqueCombination = Set[Tuple[str, str, str]]

# Helper functions
def get_valid_accounts(ou_map: OuMap) -> List[str]:
    valid_accounts = []
    for ou in ou_map.values():
        for child in ou["children"]:
            if child["type"] == "ACCOUNT":
                valid_accounts.append(child["name"])
    return valid_accounts

def get_ignore_accounts(manifest_file: ManifestFile, ou_map: OuMap) -> Set[str]:
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
    return ignore_accounts

def get_unique_combinations(
    manifest_file: ManifestFile,
    sso_user_map: SsoMap,
    sso_group_map: SsoMap,
    permission_set_map: SsoMap,
    ou_map: OuMap,
    valid_accounts: List[str],
    ignore_accounts: Set[str]
) -> UniqueCombination:
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
            valid_targets = [name for name in target_names if name not in ignore_accounts and name in valid_accounts]
        elif rule["target_type"] == "OU":
            valid_targets = [
                account["name"] for ou_name in target_names if ou_name in ou_map
                for account in ou_map[ou_name]["children"] if account["name"] not in ignore_accounts and account["name"] in valid_accounts
            ]

        unique_combinations.update((rule["principal_name"], rule["permission_set_name"], target) for target in valid_targets)
    
    return unique_combinations

# Test cases
@pytest.mark.run(order=1)
@pytest.mark.parametrize("setup_aws_environment, manifest_filename", [
    ("aws_org_1.json", "single_rule_invalid_target_type.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_target_type.yaml"),
    ("aws_org_1.json", "single_rule_invalid_access_type.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_access_type.yaml"),
    ("aws_org_1.json", "single_rule_missing_permission_set_name.yaml"),
    ("aws_org_1.json", "multiple_rules_missing_permission_set_name.yaml"),
    ("aws_org_1.json", "single_rule_missing_principal_name.yaml"),
    ("aws_org_1.json", "multiple_rules_missing_principal_name.yaml"),
    ("aws_org_1.json", "single_rule_invalid_principal_type.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_principal_type.yaml"),
    ("aws_org_1.json", "single_rule_invalid_rule_type.yaml"),
    ("aws_org_1.json", "single_rule_invalid_rule_type_datatype.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_rule_type.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_rule_type_datatype.yaml")

], indirect=["setup_aws_environment"])
def test_rules_invalid_manifest_schema(setup_aws_environment: AwsEnvironment, manifest_filename: str) -> None:
    # Arrange

    # Load manfiest files
    manifest_definition_filepath = os.path.join(
        CWD,
        "..",
        "configs",
        "manifests",
        "invalid_schema",
        manifest_filename,
    )

    # Assert
    with pytest.raises(jsonschema.ValidationError):
        # Act
        AwsAccessResolver(
            MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath
        )

@pytest.mark.run(order=2)
@pytest.mark.parametrize("setup_aws_environment, manifest_filename", [
    ("aws_org_1.json", "multiple_rules_valid.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_some_ous.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_all_ous.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_some_accounts.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_all_accounts.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_some_permission_sets.yaml"),
    ("aws_org_1.json", "multiple_rules_invalid_all_permission_sets.yaml"),
], indirect=["setup_aws_environment"])
def test_rules_valid_manifest_schema(setup_aws_environment: AwsEnvironment, manifest_filename: str) -> None:
    # Load AWS env definitions
    ou_map = convert_list_to_dict(setup_aws_environment["aws_organization_definitions"], "name")
    sso_user_map = convert_list_to_dict(setup_aws_environment["aws_sso_user_definitions"], "username")
    sso_group_map = convert_list_to_dict(setup_aws_environment["aws_sso_group_definitions"], "name")
    permission_set_map = convert_list_to_dict(setup_aws_environment["aws_permission_set_definitions"], "name")

    # Load manfiest files
    manifest_definition_filepath = os.path.join(
        CWD,
        "..",
        "configs",
        "manifests",
        "valid_schema",
        manifest_filename,
    )
    manifest_file = load_file(manifest_definition_filepath)
    aws_access_resolver = AwsAccessResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)

    valid_accounts = get_valid_accounts(ou_map)
    ignore_accounts = get_ignore_accounts(manifest_file, ou_map)
    unique_combinations = get_unique_combinations(manifest_file, sso_user_map, sso_group_map, permission_set_map, ou_map, valid_accounts, ignore_accounts)

    # Assert the length of unique combinations matches the successful RBAC assignments
    assert len(unique_combinations) == len(aws_access_resolver.successful_rbac_assignments)
