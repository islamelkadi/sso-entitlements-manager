"""
Module for resolving AWS resources and creating access
control assignments based on ingested customer manifest file.
"""

import itertools
from typing import Optional
import boto3

# Global constants
OU_TARGET_TYPE_LABEL = "OU"
ACCOUNT_TARGET_TYPE_LABEL = "ACCOUNT"
USER_PRINCIPAL_TYPE_LABEL = "USER"
GROUP_PRINCIPAL_TYPE_LABEL = "GROUP"


class AwsIdentityCenterManager:
    """
    Class for resolving AWS resources and creating RBAC (Role-Based Access Control)
    assignments based on a manifest file.
    """

    def __init__(self) -> None:
        """
        Initializes AwsAccessControlResolver with the provided identity store ARN.

        Args:
            identity_store_arn (str): The ARN of the AWS Identity Store.
        """
        self.rbac_rules = []

        self.invalid_manifest_rules_report = []
        self._invalid_manifest_file_ou_names = []
        self._invalid_manifest_file_account_names = []
        self._invalid_manifest_file_group_names = []
        self._invalid_manifest_file_user_names = []
        self._invalid_manifest_file_permission_sets = []

        self._local_account_assignments = []
        self._current_account_assignments = []

        self.account_name_id_map = {}
        self.ou_accounts_map = {}

        self.exclude_sso_users = []
        self.exclude_sso_groups = []
        self.exclude_permission_sets = []

        self._sso_admin_client = boto3.client("sso-admin")
        self._identity_store_client = boto3.client("identitystore")


    def _describe_identity_center_instance(self) -> None:
        iam_identity_center_details = self._sso_admin_client.list_instances()["Instances"][0]
        self.identity_store_id = iam_identity_center_details["IdentityStoreId"]
        self.identity_store_arn = iam_identity_center_details["InstanceArn"]

    def _map_sso_groups(self) -> None:
        """
        Lists all groups in the identity store and maps DisplayName to GroupId.
        """
        current_sso_groups = []
        groups_paginator = self._identity_store_client.get_paginator("list_groups")
        for page in groups_paginator.paginate(IdentityStoreId=self.identity_store_id):
            current_sso_groups.extend(page["Groups"])

        self.sso_groups = {}
        for group in current_sso_groups:
            if group["DisplayName"] not in self.exclude_sso_groups:
                self.sso_groups[group["DisplayName"]] = group["GroupId"]

    def _map_sso_users(self) -> None:
        """
        Lists all users in the identity store and maps UserName to UserId.
        """
        current_sso_users = []
        sso_users_pagniator = self._identity_store_client.get_paginator("list_users")
        sso_users_pages = sso_users_pagniator.paginate(IdentityStoreId=self.identity_store_id)
        for page in sso_users_pages:
            current_sso_users.extend(page["Users"])

        self.sso_users = {}
        for user in current_sso_users:
            if user["UserName"] not in self.exclude_sso_users:
                self.sso_users[user["UserName"]] = user["UserId"]

    def _map_permission_sets(self) -> None:
        """
        Lists all permission sets and maps Name to PermissionSetArn.
        """
        current_permission_sets = []
        permission_sets_paginator = self._sso_admin_client.get_paginator("list_permission_sets")
        permission_sets_pages = permission_sets_paginator.paginate(InstanceArn=self.identity_store_arn)
        for page in permission_sets_pages:
            current_permission_sets.extend(page["PermissionSets"])

        described_current_permission_sets = []
        for permission_set in current_permission_sets:
            permission_set_info = self._sso_admin_client.describe_permission_set(InstanceArn=self.identity_store_arn, PermissionSetArn=permission_set)
            described_current_permission_sets.append(permission_set_info.get("PermissionSet"))

        self.permission_sets = {}
        for permission_set in described_current_permission_sets:
            if permission_set["Name"] not in self.exclude_permission_sets:
                self.permission_sets[permission_set["Name"]] = permission_set["PermissionSetArn"]


    def _list_current_account_assignments(self) -> None:
        """
        Lists the current account assignments for the principals in the identity store.
        """
        principal_type_map = {"USER": self.sso_users.values(), "GROUP": self.sso_groups.values()}
        principal_assignments_paginator = self._sso_admin_client.get_paginator("list_account_assignments_for_principal")

        for principal_type, principals in principal_type_map.items():
            for principal_id in principals:
                assignments_iterator = principal_assignments_paginator.paginate(PrincipalId=principal_id, InstanceArn=self.identity_store_arn, PrincipalType=principal_type)
                for page in assignments_iterator:
                    self._current_account_assignments.extend(page["AccountAssignments"])

        for i, _ in enumerate(self._current_account_assignments):
            self._current_account_assignments[i]["InstanceArn"] = self.identity_store_arn
            self._current_account_assignments[i]["TargetType"] = "AWS_ACCOUNT"
            self._current_account_assignments[i]["TargetId"] = self._current_account_assignments[i].pop("AccountId")

    def _generate_invalid_assignments_report(self) -> None:
        """
        Generates a report of invalid assignments by combining all invalid entries.
        """
        self.invalid_manifest_rules_report = (
            self._invalid_manifest_file_ou_names + self._invalid_manifest_file_account_names + self._invalid_manifest_file_group_names + self._invalid_manifest_file_user_names + self._invalid_manifest_file_permission_sets
        )

    def _generate_rbac_assignments(self) -> None:
        """
        Generates RBAC assignments based on the manifest rules.
        """

        def validate_aws_resource(rule_number: int, resource_name: str, resource_type: str) -> Optional[str]:
            """
            Validates if the provided AWS resource is valid and returns its ID if valid.

            Args:
                rule_number (int): The rule number from the manifest.
                resource_name (str): The name of the resource.
                resource_type (str): The type of the resource.

            Returns:
                Optional[str]: The resource ID if valid, None otherwise.
            """
            resource_maps = {
                OU_TARGET_TYPE_LABEL: (self.ou_accounts_map, self._invalid_manifest_file_ou_names),
                ACCOUNT_TARGET_TYPE_LABEL: (self.account_name_id_map, self._invalid_manifest_file_account_names),
                GROUP_PRINCIPAL_TYPE_LABEL: (self.sso_groups, self._invalid_manifest_file_group_names),
                USER_PRINCIPAL_TYPE_LABEL: (self.sso_users, self._invalid_manifest_file_user_names),
                "permission_set": (self.permission_sets, self._invalid_manifest_file_permission_sets),
            }

            resource_map, invalid_set = resource_maps[resource_type]
            if resource_name not in resource_map:
                invalid_set.append(
                    {
                        "rule_number": rule_number,
                        "resource_type": resource_type,
                        "resource_name": resource_name,
                    }
                )
                return None

            return resource_map[resource_name]

        def add_unique_assignment(target_id: str) -> None:
            """
            Adds a unique assignment to the list of resolved account assignments.

            Args:
                target_id (str): The target ID for the assignment.
            """
            assignment = {"TargetId": target_id, "TargetType": "AWS_ACCOUNT", "PrincipalId": rule["principal_id"], "PrincipalType": rule["principal_type"], "PermissionSetArn": rule["permission_set_arn"], "InstanceArn": self.identity_store_arn}

            if assignment not in self._local_account_assignments:
                self._local_account_assignments.append(assignment)

        for i, rule in enumerate(self.rbac_rules):
            rule["rule_number"] = i
            rule["principal_id"] = validate_aws_resource(rule["rule_number"], rule["principal_name"], rule["principal_type"])
            rule["permission_set_arn"] = validate_aws_resource(rule["rule_number"], rule["permission_set_name"], "permission_set")
            if not (rule["principal_id"] and rule["permission_set_arn"]):
                continue

            valid_target_names = [name for name in rule["target_names"] if validate_aws_resource(rule["rule_number"], name, rule["target_type"])]

            if rule["target_type"] == OU_TARGET_TYPE_LABEL:
                for target in valid_target_names:
                    ou_aws_accounts = self.ou_accounts_map[target]
                    for account in ou_aws_accounts:
                        add_unique_assignment(account["Id"])
            else:
                for target in valid_target_names:
                    target_id = self.account_name_id_map[target]
                    add_unique_assignment(target_id)

    def _execute_rbac_assignments(self) -> None:
        """
        Executes the RBAC assignments by creating and deleting account assignments as necessary.
        """

        self.assignments_to_create = []
        assignments_to_create = list(itertools.filterfalse(lambda i: i in self._current_account_assignments, self._local_account_assignments))
        for assignment in assignments_to_create:
            self.assignments_to_create.append(assignment)
            self._sso_admin_client.create_account_assignment(**assignment)

        self.assignments_to_delete = []
        assignments_to_delete = list(itertools.filterfalse(lambda i: i in self._local_account_assignments, self._current_account_assignments))
        for assignment in assignments_to_delete:
            self.assignments_to_delete.append(assignment)
            self._sso_admin_client.delete_account_assignment(**assignment)


    def run_access_control_resolver(self) -> None:
        """
        Runs the full access control resolver process: listing current assignments,
        generating new assignments, generating an invalid assignments report,
        and executing the assignments.
        """
        self._describe_identity_center_instance()
        self._map_sso_users()
        self._map_sso_groups()
        self._map_permission_sets()
        self._list_current_account_assignments()
        self._generate_rbac_assignments()
        self._generate_invalid_assignments_report()
        self._execute_rbac_assignments()

