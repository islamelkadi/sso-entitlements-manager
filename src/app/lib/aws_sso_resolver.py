import os
import jsonschema
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
        self._excluded_ou_names = []
        self._excluded_account_names = []

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

    def _is_valid_aws_resource(self, resource_name: str, resource_type: str) -> bool:
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
        bool
            True if the resource is valid, False otherwise.

        Usage:
        ------
        is_valid = self._is_valid_aws_resource("resource_name", "resource_type")
        """
        if resource_type == self._ou_target_type and resource_name not in self._aws_organizations.ou_account_map:
            return False

        if resource_type == self._account_target_type and resource_name not in self._aws_organizations.account_map:
            return False

        if resource_type == self._group_principal_type and resource_name not in self._aws_identitycenter.sso_groups:
            return False

        if resource_type == self._user_principal_type and resource_name not in self._aws_identitycenter.sso_users:
            return False

        if resource_type == "permission_set" and resource_name not in self._aws_identitycenter.permission_sets:
            return False
        
        return True

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

    def _generate_account_assignments(self, rule):

        sso_users = self._aws_identitycenter.sso_users
        sso_groups = self._aws_identitycenter.sso_groups
        permission_sets = self._aws_identitycenter.permission_sets

        assignments = []
        permission_set_arn = permission_sets[rule["permission_set_name"]]["PermissionSetArn"]
        sso_principal_id = (
            sso_groups[rule["principal_name"]]["GroupId"] if rule["principal_type"] == self._group_principal_type
            else sso_users[rule["principal_name"]]["UserId"]
        )
        
        valid_target_names = []
        for name in rule["target_names"]:
            if self._is_valid_aws_resource(name, rule["target_type"]):
                valid_target_names.append(name)
        
        if rule["target_type"] == self._ou_target_type:
            for target in valid_target_names:
                ou_aws_accounts = self._aws_organizations.ou_account_map[target]
                for account in ou_aws_accounts:
                    assignments.append({
                        "permission_set_arn": permission_set_arn,
                        "principal_id": sso_principal_id,
                        "principal_type": rule["principal_type"],
                        "target_id": account["Id"]
                    })
        else:
            for target in valid_target_names:
                assignments.append({
                    "permission_set_arn": permission_set_arn,
                    "principal_id": sso_principal_id,
                    "principal_type": rule["principal_type"],
                    "target_id": self._aws_organizations.account_map[target]["Id"]
                })
        
        return assignments

    def _create_rbac_assignments(self) -> None:
        """
        Creates RBAC assignments based on the manifest definition.

        Usage:
        ------
        aws_resolver.create_rbac_assignments()
        """

        assignments_to_create = []
        rbac_rules = self._manifest_definition.get("rules", [])
        for rule in rbac_rules:
            is_valid_sso_principal = self._is_valid_aws_resource(rule["principal_name"], rule["principal_type"])
            is_valid_permission_set = self._is_valid_aws_resource(rule["permission_set_name"], "permission_set")
            if is_valid_sso_principal and is_valid_permission_set:
                account_assignments = self._generate_account_assignments(rule)
                assignments_to_create.extend(account_assignments)

        unique_assignments = {}
        for assignment in assignments_to_create:
            assignment_tuple = tuple(assignment.items())
            if assignment_tuple not in unique_assignments:
                unique_assignments[assignment_tuple] = assignment

        unique_assignments_to_create = unique_assignments.values()
        for assignment in unique_assignments_to_create:
            self._aws_identitycenter.create_permission_set_assignment(**assignment)
