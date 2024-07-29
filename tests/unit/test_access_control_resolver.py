import os
from operator import itemgetter
from typing import Dict, List, Set, Tuple

import pytest
from app.lib.utils import load_file
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
OuMap = Dict[str, Dict[str, List[Dict[str, str]]]]

# Helper functions
def get_unique_combinations(
    rbac_rules,
    ou_map,
    sso_users_map: Dict[str, str],
    sso_groups_map: Dict[str, str],
    sso_permission_sets: Dict[str, str],
    valid_accounts: List[str],
):
    unique_combinations = []
    for rule in rbac_rules:
        if rule["principal_type"] == "USER" and rule["principal_name"] not in sso_users_map:
            continue

        if rule["principal_type"] == "GROUP" and rule["principal_name"] not in sso_groups_map:
            continue

        if rule["permission_set_name"] not in sso_permission_sets:
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
                "PermissionSetArn": sso_permission_sets[rule["permission_set_name"]],
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
def test_create_assignments(setup_aws_environment: pytest.fixture, manifest_filename: str) -> None:
    # Load manifest file
    manifest_file = load_file(os.path.join(CWD, "..", "configs", "manifests", "valid_schema", manifest_filename))

    identity_center_arn = setup_aws_environment["identity_center_arn"]
    sso_users = setup_aws_environment["sso_username_id_map"]
    sso_groups = setup_aws_environment["sso_group_name_id_map"]
    permission_sets = setup_aws_environment["sso_permissionset_name_id_map"]

    ou_accounts_map = setup_aws_environment["ou_accounts_map"]
    account_name_id_map = setup_aws_environment["account_name_id_map"]

    # Create OU & Accounts map via class
    aws_access_resolver = AwsAccessResolver(identity_center_arn)
    setattr(aws_access_resolver, "rbac_rules", manifest_file["rbac_rules"])
    setattr(aws_access_resolver, "sso_users", sso_users)
    setattr(aws_access_resolver, "sso_groups", sso_groups)
    setattr(aws_access_resolver, "permission_sets", permission_sets)
    setattr(aws_access_resolver, "ou_accounts_map", ou_accounts_map)
    setattr(aws_access_resolver, "account_name_id_map", account_name_id_map)
    aws_access_resolver.run_access_control_resolver()

    # Load AWS environment definitions
    valid_unique_named_combinations = get_unique_combinations(manifest_file["rbac_rules"], ou_accounts_map, sso_users, sso_groups, permission_sets, account_name_id_map)

    # Assert generated combinations matches the successful RBAC assignments
    sort_keys = itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
    assert sorted(valid_unique_named_combinations, key=sort_keys) == sorted(aws_access_resolver.assignments_to_create, key=sort_keys)
