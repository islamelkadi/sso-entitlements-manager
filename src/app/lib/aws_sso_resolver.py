import os
import jsonschema

# Local package & layer imports
from .aws_organizations import AwsOrganizations
from .aws_identitycentre import AwsIdentityCentre
from .utils import load_file, convert_specific_keys_to_lowercase


class AwsResolver:
    """ """

    def __init__(self, schema_definition_filepath: str, manifest_definition_filepath: str) -> None:
        
        # Initialize class vars
        self._excluded_ou_names = []
        self._excluded_account_names = []

        self._invalid_manifest_file_ou_names = set()
        self._invalid_manifest_file_account_names = set()
        self._invalid_manifest_file_group_names = set()
        self._invalid_manifest_file_user_names = set()
    
        self._root_ou_id = os.getenv("ROOT_OU_ID")
        self._identity_store_id = os.getenv("IDENTITY_STORE_ID")
        self._identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

        self._ou_target_type = os.getenv("OU_TARGET_TYPE_LABEL", "ou")
        self._account_target_type = os.getenv("OU_TARGET_TYPE_LABEL", "act")
        self._user_principal_type = os.getenv("USER_PRINCIPAL_TYPE_LABEL", "user")
        self._group_principal_type = os.getenv("GROUP_PRINCIPAL_TYPE_LABEL", "group")

        # Validate manifest against schema
        self._manifest_file_keys_to_lowercase = ["access_type", "principal_type", "target_type"]
        self._schema_definition = load_file(schema_definition_filepath)
        self._manifest_definition = convert_specific_keys_to_lowercase(load_file(manifest_definition_filepath), self._manifest_file_keys_to_lowercase)
        self._is_valid_manifest_file()

        # Instantiate class instances
        self._create_excluded_ou_account_name_list()
        self._aws_organizations = AwsOrganizations(self._root_ou_id, self._excluded_ou_names, self._excluded_account_names)
        self._aws_identitycenter = AwsIdentityCentre(self._identity_store_id, self._identity_store_arn)


    def _is_valid_manifest_file(self) -> None:
        """
        Validates the manifest definition against the schema definition.

        Returns:
        -------
        bool
            True if the manifest is valid, raises jsonschema.ValidationError otherwise.
        """
        try:
            jsonschema.validate(instance=self._manifest_definition, schema=self._schema_definition)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Validation error: {e.message}")


    def _is_valid_aws_resource(self, resource_type: str, resource_names: list = []) -> None:
        if resource_type == self._ou_target_type:
            for ou_name in resource_names:
                if ou_name not in self._aws_organizations.ou_account_map:
                    self._invalid_manifest_file_ou_names.add(ou_name)
        elif resource_type == self._account_target_type:
            for account_name in resource_names:
                if account_name not in self._aws_organizations.account_map:
                    self._invalid_manifest_file_account_names.add(account_name)
        elif resource_type == self._group_principal_type:
            for group_name in resource_names:
                if group_name not in self._aws_organizations.account_map:
                    self._invalid_manifest_file_group_names.add(group_name)
        elif resource_type == self._user_principal_type:
            for group_name in resource_names:
                if group_name not in self._aws_organizations.account_map:
                    self._invalid_manifest_file_user_names.add(group_name)
        else:
            raise ValueError("Unsupported AWS resource type")


    def _create_excluded_ou_account_name_list(self) -> None:
        for item in self._manifest_definition.get("ignore", []):
            target_list = self._excluded_ou_names if item["target_type"] == self._ou_target_type else self._excluded_account_names
            target_list.extend(item["target_names"])


    def create_rbac_assignments(self):
        # Get identity center params
        sso_users = self._aws_identitycenter.sso_users
        sso_groups = self._aws_identitycenter.sso_groups
        permission_sets = self._aws_identitycenter.permission_sets

        # Get manifest rules
        rbac_rules = self._manifest_definition.get("rules", [])

        abac_assignments_to_create = []
        rbac_assignments_to_create = []

        # RBAC Rules
        for rule in rbac_rules:

            target_type = rule["target_type"]
            target_names = rule["target_names"]

            principal_name = rule["principal_name"]
            principal_type = rule["principal_type"]

            principal_id = sso_groups[principal_name]["GroupId"] if principal_type == self._group_principal_type else sso_users[principal_name]["UserId"]

            permission_set_name = rule["permission_set_name"]
            permission_set_arn = permission_sets[permission_set_name]["PermissionSetArn"]

            if target_type == self._ou_target_type:
                for ou_name in target_names:
                    if ou_name not in self._invalid_manifest_file_ou_names:
                        ou_aws_accounts = self._aws_organizations.ou_account_map[ou_name]
                        for account in ou_aws_accounts:
                            rbac_assignments_to_create.append({
                                "permission_set_arn": permission_set_arn,
                                "principal_id": principal_id,
                                "principal_type": principal_type,
                                "target_id": account["Id"]
                            })
            else:
                for account_name in target_names:
                    if account_name not in self._invalid_manifest_file_account_names:
                        account_id = self._aws_organizations.account_map[account_name]["Id"]
                        rbac_assignments_to_create.append({
                            "permission_set_arn": permission_set_arn,
                            "principal_id": principal_id,
                            "principal_type": principal_type,
                            "target_id": account_id
                        })

        # Create all assignments in one go
        assignments_to_create = abac_assignments_to_create + rbac_assignments_to_create

        seen_assignments = set()
        unique_assignments_to_create = []
        for assignment in assignments_to_create:
            assignment_tuple = tuple(assignment.items())
            if assignment_tuple not in seen_assignments:
                unique_assignments_to_create.append(dict(assignment))
                seen_assignments.add(assignment_tuple)

        for assignment in unique_assignments_to_create:
            self._aws_identitycenter.create_permission_set_assignment(**assignment)
