"""
Module to interact with AWS SSO manifest files.

This module provides a class to read, validate, and process AWS SSO manifest files,
including generating lists of excluded entities and retrieving RBAC rules.

Classes:
--------
AccessManifestReader
    A class to read and process access manifest files for AWS SSO.

    Attributes:
    -----------
    excluded_ou_names: list
        List of excluded organizational units.
    excluded_account_names: list
        List of excluded account names.
    excluded_sso_user_names: list
        List of excluded SSO user names.
    excluded_sso_group_names: list
        List of excluded SSO group names.
    excluded_permission_set_names: list
        List of excluded permission set names.

    Methods:
    --------
    __init__(schema_definition_filepath: str, manifest_file_s3_uri: str) -> None
        Initializes the AccessManifestReader with the schema definition filepath and manifest file S3 URI.
    _load_sso_manifest() -> None
        Loads schema and manifest files, converts specific keys to uppercase.
    _validate_sso_manifest() -> None
        Validates the manifest against the schema.
    _generate_excluded_lists() -> None
        Creates lists of excluded OUs, account names, user principals, group principals, and permission sets.
    rbac_rules() -> list
        Returns the RBAC rules from the manifest.
"""

import jsonschema
from .utils import load_file, convert_specific_keys_to_uppercase

# Constants (typically should be uppercase to indicate they are constants)
OU_TARGET_TYPE_LABEL = "OU"
ACCOUNT_TARGET_TYPE_LABEL = "ACCOUNT"
USER_PRINCIPAL_TYPE_LABEL = "USER"
GROUP_PRINCIPAL_TYPE_LABEL = "GROUP"
PERMISSION_SET_TYPE_LABEL = "PERMISSION_SET"

class AccessManifestReader:
    """
    A class to read and process access manifest files for AWS SSO.

    This class handles loading, validating, and processing manifest files,
    including generating lists of excluded entities and retrieving RBAC rules.

    Attributes:
    -----------
    excluded_ou_names: list
        List of excluded organizational units.
    excluded_account_names: list
        List of excluded account names.
    excluded_sso_user_names: list
        List of excluded SSO user names.
    excluded_sso_group_names: list
        List of excluded SSO group names.
    excluded_permission_set_names: list
        List of excluded permission set names.

    Methods:
    --------
    __init__(schema_definition_filepath: str, manifest_file_s3_uri: str) -> None
        Initializes the AccessManifestReader with the schema definition filepath and manifest file S3 URI.
    _load_sso_manifest() -> None
        Loads schema and manifest files, converts specific keys to uppercase.
    _validate_sso_manifest() -> None
        Validates the manifest against the schema.
    _generate_excluded_lists() -> None
        Creates lists of excluded OUs, account names, user principals, group principals, and permission sets.
    rbac_rules() -> list
        Returns the RBAC rules from the manifest.
    """

    def __init__(self, schema_definition_filepath: str, manifest_definition_filepath: str) -> None:
        """
        Initializes the AccessManifestReader with the schema definition filepath and manifest file S3 URI.

        Args:
        ----
        schema_definition_filepath: str
            Path to the JSON schema definition file.
        manifest_file_s3_uri: str
            S3 URI of the manifest file.
        """
        self._schema_definition_filepath = schema_definition_filepath
        self._manifest_definition_filepath = manifest_definition_filepath
        self._manifest_file_keys_to_uppercase = ["principal_type", "target_type", "exclude_target_type"]

        self.excluded_ou_names = []
        self.excluded_account_names = []
        self.excluded_sso_user_names = []
        self.excluded_sso_group_names = []
        self.excluded_permission_set_names = []

        # Load and validate manifest on initialization
        self._load_sso_manifest()
        self._validate_sso_manifest()
        self._generate_excluded_lists()

    def _load_sso_manifest(self) -> None:
        """
        Loads schema and manifest files, and converts specific keys to uppercase.

        Loads the schema definition from the given filepath and the manifest file
        from the given S3 URI. Converts specified keys in the manifest data to uppercase.
        """
        self._schema_definition = load_file(self._schema_definition_filepath)
        manifest_data = load_file(self._manifest_definition_filepath)
        self._manifest_definition = convert_specific_keys_to_uppercase(manifest_data, self._manifest_file_keys_to_uppercase)

    def _validate_sso_manifest(self) -> None:
        """
        Validates the manifest against the schema.

        Uses the JSON schema to validate the manifest data. Raises a ValidationError
        if the manifest does not conform to the schema.

        Raises:
        ------
        jsonschema.ValidationError: If the manifest is not valid according to the schema.
        """
        try:
            jsonschema.validate(instance=self._manifest_definition, schema=self._schema_definition)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Validation error: {e.message}")

    def _generate_excluded_lists(self) -> None:
        """
        Creates lists of excluded OUs, account names, user principals, group principals, and permission sets.

        Processes the manifest to populate the lists of excluded entities based on the "ignore" section
        in the manifest.
        """
        target_map = {
            OU_TARGET_TYPE_LABEL: self.excluded_ou_names,
            ACCOUNT_TARGET_TYPE_LABEL: self.excluded_account_names,
            USER_PRINCIPAL_TYPE_LABEL: self.excluded_sso_user_names,
            GROUP_PRINCIPAL_TYPE_LABEL: self.excluded_sso_group_names,
            PERMISSION_SET_TYPE_LABEL: self.excluded_permission_set_names
        }

        for item in self._manifest_definition.get("ignore", []):
            target_list = target_map.get(item["target_type"])
            target_list.extend(item["target_names"])

    @property
    def rbac_rules(self) -> list:
        """
        Returns the RBAC rules.

        Retrieves the RBAC (Role-Based Access Control) rules from the manifest data.

        Returns:
        -------
        list: A list of RBAC rules from the manifest.
        """
        return self._manifest_definition.get("rbac_rules", [])
