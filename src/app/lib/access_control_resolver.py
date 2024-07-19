"""
Module for resolving AWS resources and creating access
control assignments based on ingested customer manifest file.
"""

import os
from typing import Optional, Dict
import jsonschema
import boto3
from .ous_accounts_mapper import AwsOrganizations
from .identity_center_mapper import AwsIdentityCentre
from .utils import load_file, convert_specific_keys_to_uppercase, dict_reverse_lookup

# Global vars
OU_TARGET_TYPE_LABEL = "OU"
ACCOUNT_TARGET_TYPE_LABEL = "ACCOUNT"
USER_PRINCIPAL_TYPE_LABEL = "USER"
GROUP_PRINCIPAL_TYPE_LABEL = "GROUP"


class AwsAccessResolver:
    """
    Class for resolving AWS resources and creating RBAC assignments based on a manifest file.
    """

    def __init__(self, schema_definition_filepath: str, manifest_definition_filepath: str) -> None:
        """
        Initializes AwsAccessResolver with schema and manifest file paths.

        Args:
            schema_definition_filepath (str): Path to the schema definition file.
            manifest_definition_filepath (str): Path to the manifest definition file.
        """
        self._root_ou_id = os.getenv("ROOT_OU_ID")
        self._identity_store_id = os.getenv("IDENTITY_STORE_ID")
        self._identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

        self._schema_definition_filepath = schema_definition_filepath
        self._manifest_definition_filepath = manifest_definition_filepath

        self._excluded_ou_names = []
        self._excluded_account_names = []

        self._invalid_manifest_rules_report = []
        self._invalid_manifest_file_ou_names = []
        self._invalid_manifest_file_account_names = []
        self._invalid_manifest_file_group_names = []
        self._invalid_manifest_file_user_names = []
        self._invalid_manifest_file_permission_sets = []
        self._manifest_file_keys_to_uppercase = ["access_type", "principal_type", "target_type"]

        self.valid_named_account_assignments = []
        self.valid_resolved_account_assignments = []

        self._sso_admin_client = boto3.client("sso-admin")

        self._load_validate_sso_manifest()
        self._generate_excluded_lists()
        self._initialize_aws_environment_mappers()
        self._generate_rbac_assignments()
        self._generate_invalid_assignments_report()
        self._generate_valid_named_assignments_report()

    def _load_validate_sso_manifest(self) -> None:
        """
        Loads schema and manifest files, converts specific keys to uppercase, and validates the manifest.
        """
        # Load schema definition
        self._schema_definition = load_file(self._schema_definition_filepath)

        # Load manifest file definition and convert specific keys to
        # uppercase in manifest definition
        manifest_data = load_file(self._manifest_definition_filepath)
        self._manifest_definition = convert_specific_keys_to_uppercase(manifest_data, self._manifest_file_keys_to_uppercase)

        # Validate manifest against schema
        try:
            jsonschema.validate(instance=self._manifest_definition, schema=self._schema_definition)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Validation error: {e.message}")

    def _generate_excluded_lists(self) -> None:
        """
        Creates lists of excluded organizational units (OUs) and account names.
        """
        for item in self._manifest_definition.get("ignore", []):
            if item["target_type"] == OU_TARGET_TYPE_LABEL:
                self._excluded_ou_names.extend(item["target_names"])
            else:
                self._excluded_account_names.extend(item["target_names"])

    def _initialize_aws_environment_mappers(self) -> None:
        """
        Initializes AWS Organizations and Identity Center mappers.
        """
        self._aws_identitycenter = AwsIdentityCentre(self._identity_store_id, self._identity_store_arn)
        self._aws_organizations = AwsOrganizations(self._root_ou_id, self._excluded_ou_names, self._excluded_account_names)

    def _is_valid_aws_resource(self, rule_number: int, resource_name: str, resource_type: str) -> Optional[str]:
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
                self._aws_organizations.ou_name_accounts_details_map,
                self._invalid_manifest_file_ou_names,
            ),
            ACCOUNT_TARGET_TYPE_LABEL: (
                self._aws_organizations.account_name_id_map,
                self._invalid_manifest_file_account_names,
            ),
            GROUP_PRINCIPAL_TYPE_LABEL: (
                self._aws_identitycenter.sso_groups,
                self._invalid_manifest_file_group_names,
            ),
            USER_PRINCIPAL_TYPE_LABEL: (
                self._aws_identitycenter.sso_users,
                self._invalid_manifest_file_user_names,
            ),
            "permission_set": (
                self._aws_identitycenter.permission_sets,
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

    def _generate_invalid_assignments_report(self, sort_key: str = "rule_number") -> None:
        """
        Generates a report of invalid assignments.

        Args:
            sort_key (str, optional): Key to sort invalid assignments. Defaults to "rule_number".
        """
        self._invalid_manifest_rules_report = (
            self._invalid_manifest_file_ou_names + self._invalid_manifest_file_account_names + self._invalid_manifest_file_group_names + self._invalid_manifest_file_user_names + self._invalid_manifest_file_permission_sets
        )
        self._invalid_manifest_rules_report.sort(key=lambda x: x.get(sort_key))

    def _generate_rbac_assignments(self) -> None:
        """
        Creates RBAC assignments based on the manifest rules.
        """

        def add_unique_assignment(target_id: str, base_item: Dict) -> None:
            assignment = {"TargetId": target_id, **base_item}
            if assignment not in self.valid_resolved_account_assignments:
                self.valid_resolved_account_assignments.append(assignment)

        rbac_rules = self._manifest_definition.get("rules", [])
        for i, rule in enumerate(rbac_rules):
            rule["rule_number"] = i
            rule["principal_id"] = self._is_valid_aws_resource(rule["rule_number"], rule["principal_name"], rule["principal_type"])
            rule["permission_set_arn"] = self._is_valid_aws_resource(rule["rule_number"], rule["permission_set_name"], "permission_set")
            if not (rule["principal_id"] and rule["permission_set_arn"]):
                continue

            valid_target_names = []
            for name in rule["target_names"]:
                if self._is_valid_aws_resource(rule["rule_number"], name, rule["target_type"]):
                    valid_target_names.append(name)

            resolved_account_assignment_item = {
                "TargetType": "AWS_ACCOUNT",
                "PrincipalId": rule["principal_id"],
                "PrincipalType": rule["principal_type"],
                "PermissionSetArn": rule["permission_set_arn"],
                "InstanceArn": self._identity_store_arn,
            }

            if rule["target_type"] == OU_TARGET_TYPE_LABEL:
                for target in valid_target_names:
                    ou_aws_accounts = self._aws_organizations.ou_name_accounts_details_map[target]
                    for account in ou_aws_accounts:
                        add_unique_assignment(account["Id"], resolved_account_assignment_item)
            else:
                for target in valid_target_names:
                    target_id = self._aws_organizations.account_name_id_map[target]
                    add_unique_assignment(target_id, resolved_account_assignment_item)

    def _generate_valid_named_assignments_report(self) -> None:
        """
        Generates a report of valid named account assignments.
        """
        for assignment in self.valid_resolved_account_assignments:
            named_account_assignment_item = {
                "principal_name": dict_reverse_lookup(
                    self._aws_identitycenter.sso_groups if assignment["PrincipalType"] == GROUP_PRINCIPAL_TYPE_LABEL else self._aws_identitycenter.sso_users,
                    assignment["PrincipalId"],
                ),
                "permission_set_name": dict_reverse_lookup(
                    self._aws_identitycenter.permission_sets,
                    assignment["PermissionSetArn"],
                ),
                "target_type": "AWS_ACCOUNT",
                "principal_type": assignment["PrincipalType"],
                "account_name": dict_reverse_lookup(self._aws_organizations.account_name_id_map, assignment["TargetId"]),
            }

            if named_account_assignment_item not in self.valid_named_account_assignments:
                self.valid_named_account_assignments.append(named_account_assignment_item)
