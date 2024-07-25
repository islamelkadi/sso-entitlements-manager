"""
Module for resolving AWS resources and creating access
control assignments based on ingested customer manifest file.
"""
from operator import itemgetter
from typing import Optional, Dict
import boto3
from .utils import dict_reverse_lookup

# Global vars
OU_TARGET_TYPE_LABEL = "OU"
ACCOUNT_TARGET_TYPE_LABEL = "ACCOUNT"
USER_PRINCIPAL_TYPE_LABEL = "USER"
GROUP_PRINCIPAL_TYPE_LABEL = "GROUP"


class AwsAccessResolver:
    """
    Class for resolving AWS resources and creating RBAC assignments based on a manifest file.
    """

    def __init__(self, identity_store_arn: str) -> None:
        """
        Initializes AwsAccessResolver with schema and manifest file paths.

        Args:
            schema_definition_filepath (str): Path to the schema definition file.
            manifest_definition_filepath (str): Path to the manifest definition file.
        """

        self.rbac_rules = []
        self.identity_store_arn = identity_store_arn
        self._assignments_sort_keys = itemgetter("PrincipalType", "PrincipalId", "TargetId", "PermissionSetArn")

        self.invalid_manifest_rules_report = []
        self._invalid_manifest_file_ou_names = []
        self._invalid_manifest_file_account_names = []
        self._invalid_manifest_file_group_names = []
        self._invalid_manifest_file_user_names = []
        self._invalid_manifest_file_permission_sets = []

        self._current_account_assignments = []
        self._assignments_to_create = []
        self._assignments_to_delete = []

        self.sso_users = {}
        self.sso_groups = {}
        self.permission_sets = {}
        self.account_name_id_map = {}
        self.ou_name_accounts_details_map = {}

        self.valid_named_account_assignments = []
        self.valid_resolved_account_assignments = []

        self._sso_admin_client = boto3.client("sso-admin")

    def _generate_invalid_assignments_report(self) -> None:
        """
        Generates a report of invalid assignments.

        Args:
            sort_key (str, optional): Key to sort invalid assignments. Defaults to "rule_number".
        """
        self.invalid_manifest_rules_report = (
            self._invalid_manifest_file_ou_names + self._invalid_manifest_file_account_names + self._invalid_manifest_file_group_names + self._invalid_manifest_file_user_names + self._invalid_manifest_file_permission_sets
        )

    def _generate_valid_named_assignments_report(self) -> None:
        """
        Generates a report of valid named account assignments.
        """
        for assignment in self.valid_resolved_account_assignments:
            named_account_assignment_item = {
                "principal_name": dict_reverse_lookup(
                    self.sso_groups if assignment["PrincipalType"] == GROUP_PRINCIPAL_TYPE_LABEL else self.sso_users,
                    assignment["PrincipalId"],
                ),
                "permission_set_name": dict_reverse_lookup(
                    self.permission_sets,
                    assignment["PermissionSetArn"],
                ),
                "target_type": "AWS_ACCOUNT",
                "principal_type": assignment["PrincipalType"],
                "account_name": dict_reverse_lookup(self.account_name_id_map, assignment["TargetId"]),
            }

            if named_account_assignment_item not in self.valid_named_account_assignments:
                self.valid_named_account_assignments.append(named_account_assignment_item)

    def _generate_rbac_assignments(self) -> None:
        """
        Creates RBAC assignments based on the manifest rules.
        """

        def validate_aws_resource(rule_number: int, resource_name: str, resource_type: str) -> Optional[str]:
            """
            Validates if the provided AWS resource is valid.

            Args:
                rule_number (int): Rule number.
                resource_name (str): Name of the resource.
                resource_type (str): Type of the resource.

            Returns:
                Optional[str]: Resource ID if valid, None otherwise.
            """
            resource_maps = {
                OU_TARGET_TYPE_LABEL: (
                    self.ou_name_accounts_details_map,
                    self._invalid_manifest_file_ou_names,
                ),
                ACCOUNT_TARGET_TYPE_LABEL: (
                    self.account_name_id_map,
                    self._invalid_manifest_file_account_names,
                ),
                GROUP_PRINCIPAL_TYPE_LABEL: (
                    self.sso_groups,
                    self._invalid_manifest_file_group_names,
                ),
                USER_PRINCIPAL_TYPE_LABEL: (
                    self.sso_users,
                    self._invalid_manifest_file_user_names,
                ),
                "permission_set": (
                    self.permission_sets,
                    self._invalid_manifest_file_permission_sets,
                ),
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
            Adds a unique assignment to the list of valid resolved account assignments.

            This method creates an assignment dictionary by combining the `target_id` with 
            `base_item` and adds it to `valid_resolved_account_assignments` if it is not 
            already present in the list.

            Parameters:
            ----------
            target_id: str
                The target ID for the assignment.
            base_item: Dict
                A dictionary containing the base details for the assignment.

            Usage:
            ------
            self.add_unique_assignment("target-id", base_item_dict)
            """
            
            base_account_assignment = {
                "PrincipalId": rule["principal_id"],
                "PrincipalType": rule["principal_type"],
                "PermissionSetArn": rule["permission_set_arn"],
                "AccountId": target_id
            }

            if base_account_assignment not in self._current_account_assignments:
                base_account_assignment.pop("AccountId")
                assignment = {"TargetId": target_id, "TargetType": "AWS_ACCOUNT", "InstanceArn": self.identity_store_arn, **base_account_assignment}
                if assignment not in self.valid_resolved_account_assignments:
                    self.valid_resolved_account_assignments.append(assignment)
                    self._assignments_to_create.append(assignment)
            

        for i, rule in enumerate(self.rbac_rules):
            rule["rule_number"] = i
            rule["principal_id"] = validate_aws_resource(rule["rule_number"], rule["principal_name"], rule["principal_type"])
            rule["permission_set_arn"] = validate_aws_resource(rule["rule_number"], rule["permission_set_name"], "permission_set")
            if not (rule["principal_id"] and rule["permission_set_arn"]):
                continue

            valid_target_names = []
            for name in rule["target_names"]:
                if validate_aws_resource(rule["rule_number"], name, rule["target_type"]):
                    valid_target_names.append(name)

            if rule["target_type"] == OU_TARGET_TYPE_LABEL:
                for target in valid_target_names:
                    ou_aws_accounts = self.ou_name_accounts_details_map[target]
                    for account in ou_aws_accounts:
                        add_unique_assignment(account["Id"])
            else:
                for target in valid_target_names:
                    target_id = self.account_name_id_map[target]
                    add_unique_assignment(target_id)

    # def _execute_rbac_assignments(self) -> None:
    #     """
    #     Executes the RBAC assignments.
    #     """
    #     # Sort assignments
    #     self.valid_resolved_account_assignments.sort(key=self._assignments_sort_keys)

    #     # Create account assignment
    #     # Check if locally generated assignments exist on cloud
    #     for assignment in self.valid_resolved_account_assignments:
    #         assignment.pop("TargetType")
    #         if assignment not in self._current_account_assignments:
    #             self._sso_admin_client.create_account_assignment(**assignment)

    #     # Delete account assignment
    #     for assignment in self._current_account_assignments:
    #         if assignment not in self.valid_resolved_account_assignments:
    #             self._sso_admin_client.delete_account_assignment(**assignment)

    def _list_current_account_assignments(self) -> None:
        """
        Lists current account assignments.
        """
        # List assignments
        principal_type_map = {"USER": self.sso_users.values(), "GROUP": self.sso_groups.values()}
        principal_assignments_paginator = self._sso_admin_client.get_paginator("list_account_assignments_for_principal")
        for principal_type, principals in principal_type_map.items():
            for principal_id in principals:
                assignments_iterator = principal_assignments_paginator.paginate(
                    PrincipalId=principal_id, 
                    InstanceArn=self.identity_store_arn, 
                    PrincipalType=principal_type)
                for page in assignments_iterator:
                    self._current_account_assignments.extend(page["AccountAssignments"])
        self._current_account_assignments.sort(key=self._assignments_sort_keys)

    def run_access_control_resolver(self) -> None:
        self._list_current_account_assignments()
        self._generate_rbac_assignments()
        self._generate_invalid_assignments_report()
        self._generate_valid_named_assignments_report()
