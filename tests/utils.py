"""
Utils module for handling various utility functions related to RBAC management.

This module provides utility functions for processing and managing Role-Based Access 
Control (RBAC) rules within an AWS Organizations context. It supports operations 
such as identifying accounts to ignore, removing specified targets, and generating 
expected account assignments based on a manifest file.

Key Functions:
- get_ignore_accounts: Identifies accounts to be excluded from processing
- remove_ignored_targets: Removes specified targets from various mappings
- generate_valid_targets: Filters and validates target accounts
- generate_expected_account_assignments: Creates account assignment configurations
"""

from typing import Dict, Set, List, Any


def get_ignore_accounts(manifest_file, ou_map) -> Set[str]:
    """
    Determine which accounts should be ignored based on the manifest file and organizational unit map.

    This function processes both explicitly excluded account names and accounts
    within excluded organizational units. It builds a comprehensive set of account
    names that should be ignored during further processing.

    Args:
        manifest_file (ManifestFile): The manifest file containing RBAC rules and exclusions.
            This object is expected to have attributes for excluded account and OU names.
        ou_map (OuMap): A hierarchical map of organizational units and their child accounts.
            Used to recursively identify accounts within excluded OUs.

    Returns:
        Set[str]: A set of account names that should be ignored in subsequent operations.
            This includes both directly specified account names and accounts
            belonging to excluded organizational units.

    Example:
        # Assuming manifest_file contains excluded accounts and OUs
        ignore_accounts = get_ignore_accounts(manifest_file, ou_map)
        # ignore_accounts will contain names of accounts to be skipped
    """
    ignore_accounts = set()
    ignore_accounts.update(manifest_file.excluded_account_names)
    for ou_name in manifest_file.excluded_ou_names:
        if ou_name in ou_map:
            ignore_accounts.update(
                account["name"]
                for account in ou_map[ou_name]["children"]
                if account["type"] == "ACCOUNT"
            )
    return ignore_accounts


def remove_ignored_targets(
    manifest_file,
    ou_map,
    valid_accounts,
    sso_users_map,
    sso_groups_map,
    sso_permission_sets,
):
    """
    Remove targets specified in ignore rules from the provided mappings.

    This function processes ignore rules from the manifest file and removes
    corresponding targets from various mappings. It supports removing targets
    across different types: users, groups, permission sets, accounts, and
    organizational units.

    Args:
        manifest_file (ManifestFile): The manifest file containing RBAC rules and exclusions.
            Used to retrieve ignore rules for target removal.
        ou_map (OuMap): A map of organizational units and their child accounts.
            Used to resolve accounts within excluded organizational units.
        valid_accounts (Dict[str, str]): A dictionary mapping valid account names to their IDs.
            Accounts matching ignore rules will be removed from this mapping.
        sso_users_map (Dict[str, str]): A dictionary mapping SSO user names to their IDs.
            Users matching ignore rules will be removed from this mapping.
        sso_groups_map (Dict[str, str]): A dictionary mapping SSO group names to their IDs.
            Groups matching ignore rules will be removed from this mapping.
        sso_permission_sets (Dict[str, str]): A dictionary mapping permission set names to their ARNs.
            Permission sets matching ignore rules will be removed from this mapping.

    Note:
        This function modifies the input mappings in-place. The original dictionaries
        will be updated to remove targets specified in the ignore rules.
    """
    ignore_rules = manifest_file.get("ignore", [])
    for rule in ignore_rules:
        for target_name in rule.get("target_names", []):
            if rule["target_type"] == "USER":
                sso_users_map.pop(target_name, None)

            if rule["target_type"] == "GROUP":
                sso_groups_map.pop(target_name, None)

            if rule["target_type"] == "PERMISSION_SET":
                sso_permission_sets.pop(target_name, None)

            if rule["target_type"] == "ACCOUNT":
                valid_accounts.pop(target_name, None)

            if rule["target_type"] == "OU":
                for account in ou_map.get(target_name, []):
                    valid_accounts.pop(account["Name"], None)


def generate_valid_targets(rule, target_names, valid_accounts, ou_map) -> List[str]:
    """
    Generate a list of valid targets based on the rule and target names.

    This function filters and validates target accounts based on the rule's
    target type. It supports two target types: specific accounts and
    organizational units.

    Args:
        rule (Dict[str, Any]): The RBAC rule containing targeting information.
            Must include a 'target_type' key specifying the type of targets.
        target_names (List[str]): The list of target names from the rule.
            These names will be validated against available accounts.
        valid_accounts (Dict[str, str]): A dictionary mapping valid account names to their IDs.
            Used to filter and validate target accounts.
        ou_map (OuMap): A map of organizational units and their child accounts.
            Used to resolve accounts within organizational units.

    Returns:
        List[str]: A list of validated target account IDs.
            These are account IDs that match the rule's targeting criteria.

    Example:
        # For an ACCOUNT type rule
        valid_targets = generate_valid_targets(
            {'target_type': 'ACCOUNT'},
            ['Prod Account', 'Dev Account'],
            valid_accounts,
            ou_map
        )
    """
    valid_targets = []
    if rule["target_type"] == "ACCOUNT":
        for account_name in target_names:
            if account_name in valid_accounts:
                valid_targets.append(valid_accounts[account_name])
    elif rule["target_type"] == "OU":
        for ou_name in target_names:
            for account in ou_map.get(ou_name, []):
                if account["Name"] in valid_accounts:
                    valid_targets.append(valid_accounts[account["Name"]])
    return valid_targets


def generate_expected_account_assignments(
    manifest_file,
    ou_map,
    identity_store_arn: str,
    valid_accounts: Dict[str, str],
    sso_users_map: Dict[str, str],
    sso_groups_map: Dict[str, str],
    sso_permission_sets: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Generate the expected account assignments based on the manifest file and provided mappings.

    This function processes RBAC rules from the manifest file to create a comprehensive
    list of expected account assignments. It handles user and group principal types,
    filters invalid targets, and generates assignment configurations for AWS SSO.

    Args:
        manifest_file (ManifestFile): The manifest file containing RBAC rules.
            Used to retrieve and process role-based access control configurations.
        ou_map (OuMap): A map of organizational units and their child accounts.
            Used to resolve accounts within organizational units.
        identity_store_arn (str): The Amazon Resource Name (ARN) of the AWS SSO identity store.
            Required for creating account assignments.
        valid_accounts (Dict[str, str]): A dictionary mapping valid account names to their IDs.
            Used to validate and resolve target accounts.
        sso_users_map (Dict[str, str]): A dictionary mapping SSO user names to their IDs.
            Used to resolve user principals for assignments.
        sso_groups_map (Dict[str, str]): A dictionary mapping SSO group names to their IDs.
            Used to resolve group principals for assignments.
        sso_permission_sets (Dict[str, str]): A dictionary mapping permission set names to their ARNs.
            Used to resolve permission sets for assignments.

    Returns:
        List[Dict[str, Any]]: A list of expected account assignment dictionaries.
            Each dictionary represents a unique account assignment with details
            such as principal ID, principal type, permission set ARN, and target account.

    Note:
        - Skips rules with invalid principals or permission sets
        - Ensures no duplicate assignments are generated
        - Supports both user and group-based assignments

    Example:
        # Generate account assignments based on RBAC manifest
        expected_assignments = generate_expected_account_assignments(
            manifest_file, ou_map, identity_store_arn,
            valid_accounts, sso_users_map, sso_groups_map, sso_permission_sets
        )
    """
    remove_ignored_targets(
        manifest_file,
        ou_map,
        valid_accounts,
        sso_users_map,
        sso_groups_map,
        sso_permission_sets,
    )

    expected_assignments = []
    rbac_rules = manifest_file.get("rbac_rules", [])
    for rule in rbac_rules:
        if (
            rule["principal_type"] == "USER"
            and rule["principal_name"] not in sso_users_map
        ):
            continue

        if (
            rule["principal_type"] == "GROUP"
            and rule["principal_name"] not in sso_groups_map
        ):
            continue

        if rule["permission_set_name"] not in sso_permission_sets:
            continue

        target_names = rule.get("target_names", [])
        valid_targets = generate_valid_targets(
            rule, target_names, valid_accounts, ou_map
        )

        for target in valid_targets:
            target_assignment_item = {
                "PrincipalId": sso_users_map[rule["principal_name"]]
                if rule["principal_type"] == "USER"
                else sso_groups_map[rule["principal_name"]],
                "PrincipalType": rule["principal_type"],
                "PermissionSetArn": sso_permission_sets[rule["permission_set_name"]],
                "TargetId": target,
                "TargetType": "AWS_ACCOUNT",
                "InstanceArn": identity_store_arn,
            }

            if target_assignment_item not in expected_assignments:
                expected_assignments.append(target_assignment_item)

    return expected_assignments
