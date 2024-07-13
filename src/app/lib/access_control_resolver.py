"""
Module for resolving AWS resources and creating access
control assignments based on ingested customer manifest file.
"""

import os
import time
from typing import Optional, Union, List, Dict
import jsonschema
import boto3
from .ous_accounts_mapper import AwsOrganizations
from .identity_center_mapper import AwsIdentityCentre
from .utils import load_file, convert_specific_keys_to_uppercase, dict_reverse_lookup


class AwsAccessResolver:
    """
    Class for resolving AWS resources and creating RBAC assignments based on a manifest file.
    """

    def __init__(
        self, schema_definition_filepath: str, manifest_definition_filepath: str
    ) -> None:
        """
        Initializes AwsAccessResolver with schema and manifest file paths.

        Args:
            schema_definition_filepath (str): Path to the schema definition file.
            manifest_definition_filepath (str): Path to the manifest definition file.
        """
        self._initialize_class_attributes()
        self._load_environment_variables()
        self._load_schema_and_manifest(
            schema_definition_filepath, manifest_definition_filepath
        )
        self._validate_manifest()
        self._create_excluded_lists()
        self._initialize_aws_environment_mappers()
        self._create_rbac_assignments()
        self._generate_invalid_assignments_report()

    def _initialize_class_attributes(self) -> None:
        """
        Initializes various attributes used by AwsAccessResolver.
        """
        self._sso_admin_client = boto3.client("sso-admin")
        self._account_assignments_paginator = self._sso_admin_client.get_paginator(
            "list_account_assignments"
        )

        self._excluded_ou_names = []
        self._excluded_account_names = []

        self._invalid_manifest_rules_report = []
        self._invalid_manifest_file_ou_names = []
        self._invalid_manifest_file_account_names = []
        self._invalid_manifest_file_group_names = []
        self._invalid_manifest_file_user_names = []
        self._invalid_manifest_file_permission_sets = []

        self.failed_rbac_assignments = []
        self.successful_rbac_assignments = []

    def _load_environment_variables(self) -> None:
        """
        Loads required environment variables for the resolver.
        """
        self._root_ou_id = os.getenv("ROOT_OU_ID")
        self._identity_store_id = os.getenv("IDENTITY_STORE_ID")
        self._identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

        self._ou_target_type = os.getenv("OU_TARGET_TYPE_LABEL", "OU")
        self._account_target_type = os.getenv("ACCOUNT_TARGET_TYPE_LABEL", "ACCOUNT")
        self._user_principal_type = os.getenv("USER_PRINCIPAL_TYPE_LABEL", "USER")
        self._group_principal_type = os.getenv("GROUP_PRINCIPAL_TYPE_LABEL", "GROUP")

        self._manifest_file_keys_to_uppercase = [
            "access_type",
            "principal_type",
            "target_type",
        ]

    def _load_schema_and_manifest(
        self, schema_definition_filepath: str, manifest_definition_filepath: str
    ) -> None:
        """
        Loads schema and manifest files, converting specific keys to uppercase.

        Args:
            schema_definition_filepath (str): Path to the schema definition file.
            manifest_definition_filepath (str): Path to the manifest definition file.
        """
        self._schema_definition = load_file(schema_definition_filepath)
        self._manifest_definition = convert_specific_keys_to_uppercase(
            load_file(manifest_definition_filepath),
            self._manifest_file_keys_to_uppercase,
        )

    def _validate_manifest(self) -> None:
        """
        Validates the manifest file against the schema definition.

        Raises:
            jsonschema.ValidationError: If the manifest file is not valid.
        """
        try:
            jsonschema.validate(
                instance=self._manifest_definition, schema=self._schema_definition
            )
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Validation error: {e.message}")

    def _create_excluded_lists(self) -> None:
        """
        Creates lists of excluded organizational units (OUs) and account names.
        """
        for item in self._manifest_definition.get("ignore", []):
            if item["target_type"] == self._ou_target_type:
                self._excluded_ou_names.extend(item["target_names"])
            else:
                self._excluded_account_names.extend(item["target_names"])

    def _initialize_aws_environment_mappers(self) -> None:
        """
        Initializes AWS Organizations and Identity Center mappers.
        """
        self._aws_organizations = AwsOrganizations(
            self._root_ou_id, self._excluded_ou_names, self._excluded_account_names
        )
        self._aws_identitycenter = AwsIdentityCentre(
            self._identity_store_id, self._identity_store_arn
        )

    def _list_existing_assignments(
        self, account_id: str, instance_arn: str, permission_set_arn: str
    ) -> List[Dict[str, str]]:
        """
        Lists existing account assignments for a given account, instance, and permission set.

        Args:
            account_id (str): AWS account ID.
            instance_arn (str): Instance ARN.
            permission_set_arn (str): Permission set ARN.

        Returns:
            List[Dict[str, str]]: List of existing account assignments.
        """
        paginator = self._account_assignments_paginator.paginate(
            AccountId=account_id,
            InstanceArn=instance_arn,
            PermissionSetArn=permission_set_arn,
        )
        existing_assignments = []
        for page in paginator:
            existing_assignments.extend(page["AccountAssignments"])
        return existing_assignments

    def _check_assignment_exists(
        self, assignment: Dict[str, str], existing_assignments: List[Dict[str, str]]
    ) -> bool:
        """
        Checks if a given assignment already exists.

        Args:
            assignment (Dict[str, str]): Assignment to check.
            existing_assignments (List[Dict[str, str]]):List of existing assignments.

        Returns:
            bool: True if assignment exists, False otherwise.
        """
        check_assignment = {
            "AccountId": assignment["TargetId"],
            "PermissionSetArn": assignment["PermissionSetArn"],
            "PrincipalId": assignment["PrincipalId"],
            "PrincipalType": assignment["PrincipalType"],
        }
        return check_assignment in existing_assignments

    def _is_valid_aws_resource(
        self, rule_number: int, resource_name: str, resource_type: str
    ) -> Optional[str]:
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
            self._ou_target_type: (
                self._aws_organizations.ou_name_accounts_details_map,
                self._invalid_manifest_file_ou_names,
            ),
            self._account_target_type: (
                self._aws_organizations.account_name_id_map,
                self._invalid_manifest_file_account_names,
            ),
            self._group_principal_type: (
                self._aws_identitycenter.sso_groups,
                self._invalid_manifest_file_group_names,
            ),
            self._user_principal_type: (
                self._aws_identitycenter.sso_users,
                self._invalid_manifest_file_user_names,
            ),
            "permission_set": (
                self._aws_identitycenter.permission_sets,
                self._invalid_manifest_file_permission_sets,
            ),
        }

        if resource_type not in resource_maps:
            raise ValueError("Unsupported resource type")

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

    def _generate_account_assignments(
        self, rule: Dict
    ) -> List[Dict[str, Union[str, List[str]]]]:
        """
        Generates account assignments based on the given rule.

        Args:
            rule (Dict): Rule definition.

        Returns:
            List[Dict[str, Union[str, List[str]]]]: List of generated account assignments.
        """
        valid_target_names = [
            name
            for name in rule["target_names"]
            if self._is_valid_aws_resource(
                rule["rule_number"], name, rule["target_type"]
            )
        ]
        assignments = []

        if rule["target_type"] == self._ou_target_type:
            for target in valid_target_names:
                ou_aws_accounts = self._aws_organizations.ou_name_accounts_details_map[
                    target
                ]
                for account in ou_aws_accounts:
                    assignments.append(
                        {
                            "TargetId": account["Id"],
                            "PrincipalId": rule["principal_id"],
                            "PrincipalType": rule["principal_type"],
                            "PermissionSetArn": rule["permission_set_arn"],
                        }
                    )
        else:
            for target in valid_target_names:
                assignments.append(
                    {
                        "TargetId": self._aws_organizations.account_name_id_map[target],
                        "PrincipalId": rule["principal_id"],
                        "PrincipalType": rule["principal_type"],
                        "PermissionSetArn": rule["permission_set_arn"],
                    }
                )
        return assignments

    def _generate_invalid_assignments_report(
        self, sort_key: str = "rule_number"
    ) -> None:
        """
        Generates a report of invalid assignments.

        Args:
            sort_key (str, optional): Key to sort invalid assignments. Defaults to "rule_number".
        """
        self._invalid_manifest_rules_report = (
            self._invalid_manifest_file_ou_names
            + self._invalid_manifest_file_account_names
            + self._invalid_manifest_file_group_names
            + self._invalid_manifest_file_user_names
            + self._invalid_manifest_file_permission_sets
        )
        self._invalid_manifest_rules_report.sort(key=lambda x: x.get(sort_key))

    def _create_rbac_assignments(self) -> None:
        """
        Creates RBAC assignments based on the manifest rules.
        """
        assignments_to_create = []
        rbac_rules = self._manifest_definition.get("rules", [])
        for i, rule in enumerate(rbac_rules):
            rule["rule_number"] = i
            rule["principal_id"] = self._is_valid_aws_resource(
                rule["rule_number"], rule["principal_name"], rule["principal_type"]
            )
            rule["permission_set_arn"] = self._is_valid_aws_resource(
                rule["rule_number"], rule["permission_set_name"], "permission_set"
            )
            if rule["principal_id"] and rule["permission_set_arn"]:
                account_assignments = self._generate_account_assignments(rule)
                assignments_to_create.extend(account_assignments)

        unique_assignments = {}
        for assignment in assignments_to_create:
            assignment_tuple = tuple(assignment.items())
            if assignment_tuple not in unique_assignments:
                unique_assignments[assignment_tuple] = assignment

        unique_assignments_to_create = unique_assignments.values()
        for assignment in unique_assignments_to_create:
            assignment["TargetType"] = "AWS_ACCOUNT"
            assignment["InstanceArn"] = self._identity_store_arn
            existing_assignments = self._list_existing_assignments(
                account_id=assignment["TargetId"],
                instance_arn=assignment["InstanceArn"],
                permission_set_arn=assignment["PermissionSetArn"],
            )

            if not self._check_assignment_exists(assignment, existing_assignments):
                self._handle_assignment_creation(assignment)

    def _handle_assignment_creation(self, assignment: Dict) -> None:
        """
        Handles the creation of a single account assignment.

        Args:
            assignment (Dict): Account assignment details.
        """
        account_assignment_response = self._sso_admin_client.create_account_assignment(
            **assignment
        )["AccountAssignmentCreationStatus"]
        attempts = 0
        while account_assignment_response["Status"] == "IN_PROGRESS" and attempts < 3:
            time.sleep(1)
            account_assignment_response = (
                self._sso_admin_client.describe_account_assignment_creation_status(
                    InstanceArn=assignment["InstanceArn"],
                    AccountAssignmentCreationRequestId=account_assignment_response[
                        "RequestId"
                    ],
                )["AccountAssignmentCreationStatus"]
            )
            attempts += 1

        account_assignment_result = {
            "status": account_assignment_response["Status"],
            "account": dict_reverse_lookup(
                self._aws_organizations.account_name_id_map, assignment["TargetId"]
            ),
            "principal_type": assignment["PrincipalType"],
            "principal_name": dict_reverse_lookup(
                self._aws_identitycenter.sso_groups, assignment["PrincipalId"]
            ),
            "permission_set_name": dict_reverse_lookup(
                self._aws_identitycenter.permission_sets, assignment["PermissionSetArn"]
            ),
        }

        if account_assignment_response["Status"] == "SUCCEEDED":
            self.successful_rbac_assignments.append(account_assignment_result)
        else:
            account_assignment_result[
                "failure_reason"
            ] = account_assignment_response.get(
                "FailureReason", "IN_PROGRESS status check attempts exceeded"
            )
            self.failed_rbac_assignments.append(account_assignment_result)
