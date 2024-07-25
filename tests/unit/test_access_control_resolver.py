# pylint: disable=R0801,W0613
"""
Unit tests to test manifest file ingestion and validate different
YAML configuration files against a JSON schema definition.

Tests:
- test_single_rule_invalid_rules_target_type:
    Validate a single rule with invalid rules target type.
- test_multiple_rules_invalid_rules_target_type:
    Validate multiple rules with invalid rules target type.
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
from operator import itemgetter
from typing import Dict, List, Set, Tuple

import boto3
import pytest
from app.lib.ous_accounts_mapper import AwsOrganizations
from app.lib.identity_center_mapper import AwsIdentityCentre
from app.lib.access_control_resolver import AwsAccessResolver
from app.lib.access_manifest_reader import AccessManifestReader


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
OuMap = Dict[str, Dict[str, List[Dict[str, str]]]]
SsoMap = Dict[str, Dict[str, str]]
ManifestFile = Dict[str, List[Dict[str, List[str]]]]
AccountAssignment = Set[Tuple[str, str, str]]


# Helper functions
def get_valid_accounts(ou_map: OuMap) -> List[str]:
    """
    Extract a list of valid account names from the organizational unit map.

    Parameters:
    ----------
        ou_map (OuMap): A dictionary representing the organizational units and their children.


    Returns:
    -------
        List[str]: A list of valid account names.
    """
    return {x["Name"]: x["Id"] for x in itertools.chain(*ou_map.values())}

def get_ignore_accounts(manifest_file: AccessManifestReader, ou_map: OuMap) -> Set[str]:
    """
    Determine which accounts should be ignored based on the manifest file
    and organizational unit map.

    Parameters:
    ----------
        manifest_file (ManifestFile): A dictionary representing the manifest file configuration.
        ou_map (OuMap): A dictionary representing the organizational units and their children.


    Returns:
    -------
        Set[str]: A set of account names to ignore.
    """
    ignore_accounts = set()
    ignore_accounts.update(manifest_file.excluded_account_names)
    for ou_name in manifest_file.excluded_ou_names:
        ignore_accounts.update(account["Name"] for account in ou_map.get(ou_name, []))
    return ignore_accounts

def get_unique_combinations(
    manifest_file: ManifestFile,
    sso_users_map: SsoMap,
    sso_groups_map: SsoMap,
    permission_sets_map: SsoMap,
    ou_map: OuMap,
    valid_accounts: List[str],
) -> AccountAssignment:
    """
    Generate a set of unique combinations of principal names, permission sets, and
    target accounts based on the manifest file.

    Parameters:
    ----------
        manifest_file (ManifestFile): A dictionary representing the manifest file configuration.
        sso_users_map (SsoMap): A dictionary mapping SSO users.
        sso_groups_map (SsoMap): A dictionary mapping SSO groups.
        permission_sets_map (SsoMap): A dictionary mapping permission sets.
        ou_map (OuMap): A dictionary representing the organizational units and their children.
        valid_accounts (List[str]): A list of valid account names.

    Returns:
    -------
        UniqueCombination: A set of unique (principal_name, permission_set_name, target) tuples.
    """
    unique_combinations = []
    for rule in manifest_file.rbac_rules:
        if rule["principal_type"] == "USER" and rule["principal_name"] not in sso_users_map:
            continue

        if rule["principal_type"] == "GROUP" and rule["principal_name"] not in sso_groups_map:
            continue

        if rule["permission_set_name"] not in permission_sets_map:
            continue


        target_names = rule["target_names"]
        if rule["target_type"] == "ACCOUNT":
            valid_targets = []
            for account_name in target_names:
                if account_name in valid_accounts:
                    valid_targets.append(valid_accounts[account_name])

        elif rule["target_type"] == "OU":
            valid_targets = []
            for ou_name in target_names:
                for account in ou_map.get(ou_name, []):
                    if account["Name"] in valid_accounts:
                        valid_targets.append(valid_accounts[account["Name"]])

        for target in valid_targets:
            target_assignment_item = {
                "PrincipalId": sso_users_map[rule["principal_name"]] if rule["principal_type"] == "USER" else sso_groups_map[rule["principal_name"]],
                "PrincipalType": rule["principal_type"],
                "PermissionSetArn": permission_sets_map[rule["permission_set_name"]],
                "TargetId": target,
                "TargetType": "AWS_ACCOUNT",
                "InstanceArn": "arn:aws:sso:::instance/ssoins-instanceId"
            }

            if target_assignment_item not in unique_combinations:
                unique_combinations.append(target_assignment_item)

    return unique_combinations


# Test cases
@pytest.mark.parametrize(
    "setup_aws_environment, manifest_filename",
    [
        ("aws_org_1.json", "multiple_rules_valid.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_ous.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_ous.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_accounts.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_accounts.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_permission_sets.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_permission_sets.yaml"),
    ],
    indirect=["setup_aws_environment"],
)
def test_create_only_new_assignments(setup_aws_environment: pytest.fixture, manifest_filename: str) -> None:
    """
    Test to validate manifest files with valid schema definitions.

    This test checks if manifest files with various valid schema
    configurations are correctly processed by the AwsAccessResolver,
    and the unique RBAC assignments are properly calculated.

    Parameters:
    ----------
        setup_aws_environment (pytest.fixture): Fixture to set up the AWS environment.
        manifest_filename (str): Name of the manifest file to validate.

    Asserts:
    -------
        The number of unique combinations matches the number of successful RBAC assignments.
    """

    # Load manifest file
    manifest_definition_filepath = os.path.join(CWD, "..", "configs", "manifests", "valid_schema", manifest_filename)
    manifest_file = AccessManifestReader(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)

    # Create OU & Accounts map via class
    aws_org = AwsOrganizations(setup_aws_environment["root_ou_id"])
    setattr(aws_org, "exclude_ou_name_list", manifest_file.excluded_ou_names)
    setattr(aws_org, "exclude_account_name_list", manifest_file.excluded_account_names)
    aws_org.run_ous_accounts_mapper()

    aws_idc = AwsIdentityCentre(setup_aws_environment["identity_center_id"], setup_aws_environment["identity_center_arn"])
    setattr(aws_idc, "exclude_sso_users", manifest_file.excluded_sso_user_names)
    setattr(aws_idc, "exclude_sso_groups", manifest_file.excluded_sso_group_names)
    setattr(aws_idc, "exclude_permission_sets", manifest_file.excluded_permission_set_names)
    aws_idc.run_identity_center_mapper()

    aws_access_resolver = AwsAccessResolver(setup_aws_environment["identity_center_arn"])
    setattr(aws_access_resolver, "rbac_rules", manifest_file.rbac_rules)
    setattr(aws_access_resolver, "sso_users", aws_idc.sso_users)
    setattr(aws_access_resolver, "sso_groups", aws_idc.sso_groups)
    setattr(aws_access_resolver, "permission_sets", aws_idc.permission_sets)
    setattr(aws_access_resolver, "account_name_id_map", aws_org.account_name_id_map)
    setattr(aws_access_resolver, "ou_accounts_map", aws_org.ou_accounts_map)
    aws_access_resolver.run_access_control_resolver()

    # Load AWS environment definitions
    valid_accounts = get_valid_accounts(aws_org.ou_accounts_map)
    ignore_accounts = get_ignore_accounts(manifest_file, aws_org.ou_accounts_map)
    target_accounts = {account_name: account_id for account_name, account_id in valid_accounts.items() if account_name not in ignore_accounts}
    valid_unique_named_combinations = get_unique_combinations(manifest_file,aws_idc.sso_users, aws_idc.sso_groups, aws_idc.permission_sets, aws_org.ou_accounts_map, target_accounts)

    # Assert generated combinations matches the successful RBAC assignments
    sort_keys = itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
    assert sorted(valid_unique_named_combinations, key=sort_keys) == sorted(aws_access_resolver.assignments_to_create, key=sort_keys)

    # Assert test generated invalid report matches class generated invalid report matches
    invalid_assignments = []
    for i, rule in enumerate(manifest_file.rbac_rules):
        # Check target names
        target_reference = list(aws_org.ou_accounts_map.keys()) if rule["target_type"] == "OU" else valid_accounts
        for target_name in rule["target_names"]:
            if target_name not in target_reference:
                invalid_assignments.append({
                    "rule_number": i,
                    "resource_type": rule["target_type"],
                    "resource_name": target_name,
                })

        # Check principal name
        target_reference = aws_idc.sso_groups.keys() if rule["principal_type"] == "GROUP" else aws_idc.sso_users.keys()
        if rule["principal_name"] not in target_reference:
            invalid_assignments.append({
                "rule_number": i,
                "resource_type": rule["principal_type"],
                "resource_name": rule["principal_name"],
            })

        # Check permission set name
        if rule["permission_set_name"] not in aws_idc.permission_sets:
            invalid_assignments.append({
                "rule_number": i,
                "resource_type": "permission_set",
                "resource_name": rule["permission_set_name"],
            })

    sort_keys = itemgetter("rule_number", "resource_type", "resource_name")
    assert sorted(invalid_assignments, key=sort_keys) == sorted(aws_access_resolver.invalid_manifest_rules_report, key=sort_keys)


@pytest.mark.parametrize(
    "setup_aws_environment, manifest_filename",
    [
        ("aws_org_1.json", "multiple_rules_valid.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_ous.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_ous.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_accounts.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_accounts.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_permission_sets.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_permission_sets.yaml"),
    ],
    indirect=["setup_aws_environment"],
)
def test_no_new_assignments(setup_aws_environment: pytest.fixture, manifest_filename: str) -> None:
    """
    Test to validate manifest files with valid schema definitions.

    This test checks if manifest files with various valid schema
    configurations are correctly processed by the AwsAccessResolver,
    and the unique RBAC assignments are properly calculated.

    Parameters:
    ----------
        setup_aws_environment (pytest.fixture): Fixture to set up the AWS environment.
        manifest_filename (str): Name of the manifest file to validate.

    Asserts:
    -------
        The number of unique combinations matches the number of successful RBAC assignments.
    """

    # Load manifest file
    manifest_definition_filepath = os.path.join(CWD, "..", "configs", "manifests", "valid_schema", manifest_filename)
    manifest_file = AccessManifestReader(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)

    # Create OU & Accounts map via class
    aws_org = AwsOrganizations(setup_aws_environment["root_ou_id"])
    setattr(aws_org, "exclude_ou_name_list", manifest_file.excluded_ou_names)
    setattr(aws_org, "exclude_account_name_list", manifest_file.excluded_account_names)
    aws_org.run_ous_accounts_mapper()

    aws_idc = AwsIdentityCentre(setup_aws_environment["identity_center_id"], setup_aws_environment["identity_center_arn"])
    setattr(aws_idc, "exclude_sso_users", manifest_file.excluded_sso_user_names)
    setattr(aws_idc, "exclude_sso_groups", manifest_file.excluded_sso_group_names)
    setattr(aws_idc, "exclude_permission_sets", manifest_file.excluded_permission_set_names)
    aws_idc.run_identity_center_mapper()

    # Load AWS environment definitions
    valid_accounts = get_valid_accounts(aws_org.ou_accounts_map)
    ignore_accounts = get_ignore_accounts(manifest_file, aws_org.ou_accounts_map)
    target_accounts = {account_name: account_id for account_name, account_id in valid_accounts.items() if account_name not in ignore_accounts}
    valid_unique_named_combinations = get_unique_combinations(manifest_file, aws_idc.sso_users, aws_idc.sso_groups, aws_idc.permission_sets, aws_org.ou_accounts_map, target_accounts)
    sso_admin_client = boto3.client("sso-admin")

    for assignment in valid_unique_named_combinations:
        sso_admin_client.create_account_assignment(
            InstanceArn="arn:aws:sso:::instance/ssoins-instanceId",
            TargetId=assignment["TargetId"],
            TargetType=assignment["TargetType"],
            PermissionSetArn=assignment["PermissionSetArn"],
            PrincipalType=assignment["PrincipalType"],
            PrincipalId=assignment["PrincipalId"],
        )

    aws_access_resolver = AwsAccessResolver(setup_aws_environment["identity_center_arn"])
    setattr(aws_access_resolver, "rbac_rules", manifest_file.rbac_rules)
    setattr(aws_access_resolver, "sso_users", aws_idc.sso_users)
    setattr(aws_access_resolver, "sso_groups", aws_idc.sso_groups)
    setattr(aws_access_resolver, "permission_sets", aws_idc.permission_sets)
    setattr(aws_access_resolver, "account_name_id_map", aws_org.account_name_id_map)
    setattr(aws_access_resolver, "ou_accounts_map", aws_org.ou_accounts_map)
    aws_access_resolver.run_access_control_resolver()

    # Assert generated combinations matches the successful RBAC assignments
    sort_keys = itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
    assert [] == aws_access_resolver.assignments_to_create

    # Assert test generated invalid report matches class generated invalid report matches
    invalid_assignments = []
    for i, rule in enumerate(manifest_file.rbac_rules):
        # Check target names
        target_reference = list(aws_org.ou_accounts_map.keys()) if rule["target_type"] == "OU" else valid_accounts
        for target_name in rule["target_names"]:
            if target_name not in target_reference:
                invalid_assignments.append({
                    "rule_number": i,
                    "resource_type": rule["target_type"],
                    "resource_name": target_name,
                })

        # Check principal name
        target_reference = aws_idc.sso_groups.keys() if rule["principal_type"] == "GROUP" else aws_idc.sso_users.keys()
        if rule["principal_name"] not in target_reference:
            invalid_assignments.append({
                "rule_number": i,
                "resource_type": rule["principal_type"],
                "resource_name": rule["principal_name"],
            })

        # Check permission set name
        if rule["permission_set_name"] not in aws_idc.permission_sets:
            invalid_assignments.append({
                "rule_number": i,
                "resource_type": "permission_set",
                "resource_name": rule["permission_set_name"],
            })

    sort_keys = itemgetter("rule_number", "resource_type", "resource_name")
    assert sorted(invalid_assignments, key=sort_keys) == sorted(aws_access_resolver.invalid_manifest_rules_report, key=sort_keys)
