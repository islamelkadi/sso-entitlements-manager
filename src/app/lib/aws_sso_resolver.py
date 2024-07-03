import os
import jsonschema

# Local package & layer imports
from .utils import load_file
from .aws_organizations import AwsOrganizations
from .aws_identitycentre import AwsIdentityCentre


class AwsResolver:
    """ """

    def __init__(self, schema_definition_filepath: str, manifest_definition_filepath: str) -> None:
        
        # Initialize class vars
        self._excluded_ou_name_list = []
        self._excluded_account_name_list = []

        self._root_ou_id = os.getenv("ROOT_OU_ID")
        self._identity_store_id = os.getenv("IDENTITY_STORE_ID")
        self._identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

        # Validate manifest against schema
        self._schema_definition = load_file(schema_definition_filepath)
        self._manifest_definition = load_file(manifest_definition_filepath)
        self._is_valid_manifest_file()

        # Instantiate class instances
        self._create_excluded_ou_account_map()
        self._aws_organizations = AwsOrganizations(self._root_ou_id, self._excluded_ou_name_list, self._excluded_account_name_list)
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

    def _create_excluded_ou_account_map(self) -> None:
        for item in self._manifest_definition.get("ignore", []):
            target_list = self._excluded_ou_name_list if item["target_type"] == "OU" else self._excluded_account_name_list
            target_list.extend(item["target_names"])
        
    def create_rbac_assignments(self):
        sso_users = self._aws_identitycenter.sso_users
        sso_groups = self._aws_identitycenter.sso_groups
        permission_sets = self._aws_identitycenter.permission_sets

        for rule in self._manifest_definition:
            print(rule)
        