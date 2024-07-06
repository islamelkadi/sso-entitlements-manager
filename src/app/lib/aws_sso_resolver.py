"""
Module for resolving AWS resources and creating access 
control assignments based on ingested customer manifest file.
"""

import os
import jsonschema
from typing import Optional
import boto3
from .aws_organizations import AwsOrganizations
from .aws_identitycentre import AwsIdentityCentre
from .utils import load_file, convert_specific_keys_to_uppercase

class AwsResolver:
    """
    Class for resolving AWS resources and creating RBAC assignments based on a manifest file.

    Attributes:
    ----------
    _excluded_ou_names: list
        List of excluded OU names.
    _excluded_account_names: list
        List of excluded account names.
    _invalid_manifest_file_ou_names: set
        Set of invalid OU names found in the manifest file.
    _invalid_manifest_file_account_names: set
        Set of invalid account names found in the manifest file.
    _invalid_manifest_file_group_names: set
        Set of invalid group names found in the manifest file.
    _invalid_manifest_file_user_names: set
        Set of invalid user names found in the manifest file.
    _invalid_manifest_file_permission_sets: set
        Set of invalid permission sets found in the manifest file.
    _root_ou_id: str
        Root OU ID from environment variables.
    _identity_store_id: str
        Identity store ID from environment variables.
    _identity_store_arn: str
        Identity store ARN from environment variables.
    _ou_target_type: str
        Target type label for OUs.
    _account_target_type: str
        Target type label for accounts.
    _user_principal_type: str
        Principal type label for users.
    _group_principal_type: str
        Principal type label for groups.
    _manifest_file_keys_to_uppercase: list
        List of keys in the manifest file to convert to lowercase.
    _schema_definition: dict
        Schema definition loaded from the schema file.
    _manifest_definition: dict
        Manifest definition loaded and processed from the manifest file.
    _aws_organizations: AwsOrganizations
        AwsOrganizations instance for managing AWS organizations.
    _aws_identitycenter: AwsIdentityCentre
        AwsIdentityCentre instance for managing AWS Identity Center.

    Methods:
    --------
    __init__(self, schema_definition_filepath: str, manifest_definition_filepath: str) -> None
        Initializes the AwsResolver instance with schema and manifest definitions.
    _is_valid_manifest_file(self) -> None
        Validates the manifest definition against the schema definition.
    _is_valid_aws_resource(self, resource_name: str, resource_type: str) -> Optional[str]
        Validates if a given AWS resource exists based on its type and name.
    _create_excluded_ou_account_name_list(self) -> None
        Creates a list of excluded OU and account names from the manifest definition.
    _generate_account_assignments(self, rule: dict) -> list[dict[str]]
        Generates a list of account assignments based on the provided rule.
    _create_rbac_assignments(self) -> None
        Creates RBAC assignments based on the manifest definition.
    """

    def __init__(self, schema_definition_filepath: str, manifest_definition_filepath: str) -> None:
        """
        Initializes the AwsResolver instance with schema and manifest definitions.

        Parameters:
        ----------
        schema_definition_filepath: str
            The file path to the schema definition.
        manifest_definition_filepath: str
            The file path to the manifest definition.

        Usage:
        ------
        aws_resolver = AwsResolver("path/to/schema.json", "path/to/manifest.json")
        """

        self._sso_admin_client = boto3.client("sso-admin")

        self._excluded_ou_names = []
        self._excluded_account_names = []

        self._invalid_manifest_file_ou_names = set()
        self._invalid_manifest_file_account_names = set()
        self._invalid_manifest_file_group_names = set()
        self._invalid_manifest_file_user_names = set()
        self._invalid_manifest_file_permission_sets = set()

        self._root_ou_id = os.getenv("ROOT_OU_ID")
        self._identity_store_id = os.getenv("IDENTITY_STORE_ID")
        self._identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

        self._ou_target_type = os.getenv("OU_TARGET_TYPE_LABEL", "OU")
        self._account_target_type = os.getenv("ACCOUNT_TARGET_TYPE_LABEL", "ACT")
        self._user_principal_type = os.getenv("USER_PRINCIPAL_TYPE_LABEL", "USER")
        self._group_principal_type = os.getenv("GROUP_PRINCIPAL_TYPE_LABEL", "GROUP")

        self._manifest_file_keys_to_uppercase = ["access_type", "principal_type", "target_type"]
        self._schema_definition = load_file(schema_definition_filepath)
        self._manifest_definition = convert_specific_keys_to_uppercase(
            load_file(manifest_definition_filepath), self._manifest_file_keys_to_uppercase
        )
        
        self._is_valid_manifest_file()
        self._create_excluded_ou_account_name_list()

        self._aws_organizations = AwsOrganizations(self._root_ou_id, self._excluded_ou_names, self._excluded_account_names)
        self._aws_identitycenter = AwsIdentityCentre(self._identity_store_id, self._identity_store_arn)

        self._create_rbac_assignments()

    def _is_valid_manifest_file(self) -> None:
        """
        Validates the manifest definition against the schema definition.

        Raises:
        ------
        jsonschema.ValidationError
            If the manifest is not valid.

        Usage:
        ------
        self._is_valid_manifest_file()
        """
        try:
            jsonschema.validate(instance=self._manifest_definition, schema=self._schema_definition)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Validation error: {e.message}")

    def _is_valid_aws_resource(self, resource_name: str, resource_type: str) -> Optional[str]:
        """
        Validates if a given AWS resource exists based on its type and name.

        Parameters:
        ----------
        resource_name: str
            The name of the AWS resource.
        resource_type: str
            The type of the AWS resource.

        Returns:
        -------
        str
            The resource identifier if the resource is valid, None otherwise.

        Usage:
        ------
        is_valid = self._is_valid_aws_resource("resource_name", "resource_type")
        """
        resource_maps = {
            self._ou_target_type: (self._aws_organizations.ou_account_map, self._invalid_manifest_file_ou_names),
            self._account_target_type: (self._aws_organizations.account_map, self._invalid_manifest_file_account_names),
            self._group_principal_type: (self._aws_identitycenter.sso_groups, self._invalid_manifest_file_group_names, "GroupId"),
            self._user_principal_type: (self._aws_identitycenter.sso_users, self._invalid_manifest_file_user_names, "UserId"),
            "permission_set": (self._aws_identitycenter.permission_sets, self._invalid_manifest_file_permission_sets)
        }

        if resource_type not in resource_maps:
            raise ValueError("Unsupported resource type")

        resource_map, invalid_set, *key = resource_maps[resource_type]
        if resource_name not in resource_map:
            invalid_set.add(resource_name)
            return None

        return resource_map[resource_name] if not key else resource_map[resource_name][key[0]]

    def _create_excluded_ou_account_name_list(self) -> None:
        """
        Creates a list of excluded OU and account names from the manifest definition.

        Usage:
        ------
        self._create_excluded_ou_account_name_list()
        """
        for item in self._manifest_definition.get("ignore", []):
            target_list = self._excluded_ou_names if item["target_type"] == self._ou_target_type else self._excluded_account_names
            target_list.extend(item["target_names"])

    def _generate_account_assignments(self, rule: dict) -> list[dict[str]]:
        """
        Generates a list of account assignments based on the provided rule.

        Parameters:
        ----------
        rule: dict
            A dictionary containing the rule for generating account assignments.
            Expected keys: "target_names", "target_type", "principal_id", "principal_type", "permission_set_arn".

        Returns:
        -------
        list
            A list of dictionaries, each representing an account assignment.

        Usage:
        ------
        rule = {
            "target_names": ["OU1", "OU2"],
            "target_type": "OU",
            "principal_id": "user-123",
            "principal_type": "USER",
            "permission_set_arn": "arn:aws:iam::aws:policy/AdministratorAccess"
        }
        assignments = self._generate_account_assignments(rule)
        """
        valid_target_names = []
        for name in rule["target_names"]:
            if self._is_valid_aws_resource(name, rule["target_type"]):
                valid_target_names.append(name)

        assignments = []
        if rule["target_type"] == self._ou_target_type:
            for target in valid_target_names:
                ou_aws_accounts = self._aws_organizations.ou_account_map[target]
                for account in ou_aws_accounts:
                    assignments.append({
                        "TargetId": account["Id"],
                        "PrincipalId": rule["principal_id"],
                        "PrincipalType": rule["principal_type"],
                        "PermissionSetArn": rule["permission_set_arn"]
                    })
        else:
            for target in valid_target_names:
                assignments.append({
                    "TargetId": self._aws_organizations.account_map[target]["Id"],
                    "PrincipalId": rule["principal_id"],
                    "PrincipalType": rule["principal_type"],
                    "PermissionSetArn": rule["permission_set_arn"]
                })

        return assignments

    def _create_rbac_assignments(self) -> None:
        """
        Creates RBAC assignments based on the manifest definition.

        Usage:
        ------
        self._create_rbac_assignments()
        """
        assignments_to_create = []
        rbac_rules = self._manifest_definition.get("rules", [])
        for rule in rbac_rules:
            rule["principal_id"] = self._is_valid_aws_resource(rule["principal_name"], rule["principal_type"])
            rule["permission_set_arn"] = self._is_valid_aws_resource(rule["permission_set_name"], "permission_set")
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
            assignment["InstanceArn"] = self._identity_store_arn
            assignment["TargetType"] = "AWS_ACCOUNT"
            self._sso_admin_client.create_account_assignment(**assignment)
