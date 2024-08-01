from typing import Dict, List, Set, Tuple, Any

def get_ignore_accounts(manifest_file, ou_map) -> Set[str]:
     """
     Determine which accounts should be ignored based on the manifest file
     and organizational unit map.
 @@ -93,13 +96,10 @@ def get_ignore_accounts(manifest_file: ManifestFile, ou_map: OuMap) -> Set[str]:
         Set[str]: A set of account names to ignore.
     """
     ignore_accounts = set()
     ignore_accounts.update(manifest_file.excluded_account_names)
     for ou_name in manifest_file.excluded_ou_names:
         if ou_name in ou_map:
             ignore_accounts.update(account["name"] for account in ou_map[ou_name]["children"] if account["type"] == "ACCOUNT")
     return ignore_accounts

def generate_expected_account_assignments(
    manifest_file,
    ou_map,
    valid_accounts: Dict[str, str],
    sso_users_map: Dict[str, str],
    sso_groups_map: Dict[str, str],
    sso_permission_sets: Dict[str, str],
):

    ignore_rules = manifest_file.get("ignore", [])
    for rule in ignore_rules:
        if rule["target_type"] == "USER":
            for user in rule["target_names"]:
                if user in sso_users_map:
                    del sso_users_map[user]

        if rule["target_type"] == "GROUP":
            for group in rule["target_names"]:
                if group in sso_groups_map:
                    del sso_groups_map[group]

        if rule["target_type"] == "PERMISSION_SET":
            for permission_set in rule["target_names"]:
                if permission_set in sso_permission_sets:
                    del sso_permission_sets[permission_set]
        
        if rule["target_type"] == "ACCOUNT":
            for account in rule["target_names"]:
                if account in valid_accounts:
                    del valid_accounts[account["Name"]]
        
        if rule["target_type"] == "OU":
            for ou_name in rule["target_names"]:
                if ou_name in ou_map:
                    for account in ou_map[ou_name]:
                        del valid_accounts[account["Name"]]

    expected_assignments = []
    rbac_rules = manifest_file.get("rbac_rules", [])
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
                "InstanceArn": "arn:aws:sso:::instance/ssoins-instanceId",
            }

            if target_assignment_item not in expected_assignments:
                expected_assignments.append(target_assignment_item)

    return expected_assignments
