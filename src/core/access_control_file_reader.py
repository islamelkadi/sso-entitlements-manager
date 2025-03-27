"""
Access Control Manifest Parser Module

This module provides a utility for reading and parsing access control 
manifest files with JSON schema validation. It enables structured 
parsing of SSO and organizational access control configurations.

Key Features:
    - JSON schema validation for manifest files
    - Parsing of access control rules
    - Generation of exclusion lists for various target types
    - Case-insensitive key processing

Warning:
    Requires properly formatted manifest and schema JSON files.
"""

import jsonschema
from src.core.utils import load_file, convert_specific_keys_to_uppercase
from src.core.constants import (
    OU_TARGET_TYPE_LABEL,
    ACCOUNT_TARGET_TYPE_LABEL,
    USER_PRINCIPAL_TYPE_LABEL,
    GROUP_PRINCIPAL_TYPE_LABEL,
    PERMISSION_SET_TYPE_LABEL,
)


class AccessControlFileReader:
    """
    A parser for access control manifest files with JSON schema validation.

    This class reads and validates an access control manifest file,
    extracting RBAC rules and generating exclusion lists for various
    target types such as organizational units, accounts, SSO users,
    groups, and permission sets.

    Args:
        manifest_definition_filepath (str): Path to the access control manifest file.
        schema_definition_filepath (str): Path to the JSON schema definition file.

    Attributes:
        _excluded_ou_names (list[str]): List of excluded organizational unit names.
        _excluded_account_names (list[str]): List of excluded account names.
        _excluded_sso_user_names (list[str]): List of excluded SSO user names.
        _excluded_sso_group_names (list[str]): List of excluded SSO group names.
        _excluded_permission_set_names (list[str]): List of excluded permission set names.

    Raises:
        jsonschema.ValidationError: If the manifest file does not conform to the schema.

    Example:
        >>> reader = AccessControlFileReader(
        ...     'path/to/manifest.json',
        ...     'path/to/schema.json'
        ... )
        >>> rbac_rules = reader.rbac_rules
        >>> excluded_ous = reader.excluded_ou_names
    """

    def __init__(
        self, manifest_definition_filepath, schema_definition_filepath
    ) -> None:
        """
        Initialize the AccessControlFileReader.

        Loads the manifest and schema files, validates the manifest,
        and generates exclusion lists for various target types.

        Args:
            manifest_definition_filepath (str): Path to the access control manifest file.
            schema_definition_filepath (str): Path to the JSON schema definition file.
        """
        self._schema_definition_filepath: str = schema_definition_filepath
        self._manifest_definition_filepath: str = manifest_definition_filepath

        # Initialize exclusion lists
        self._excluded_ou_names: list[str] = []
        self._excluded_account_names: list[str] = []
        self._excluded_sso_user_names: list[str] = []
        self._excluded_sso_group_names: list[str] = []
        self._excluded_permission_set_names: list[str] = []

        # Keys to convert to uppercase
        self._manifest_file_keys_to_uppercase: list[str] = [
            "principal_type",
            "target_type",
            "exclude_target_type",
        ]

        # Load and process manifest
        self._load_sso_manifest_file()
        self._validate_sso_manifest_file()
        self._generate_excluded_targets_lists()

    def _load_sso_manifest_file(self) -> None:
        """
        Load the SSO manifest and schema files, and converts the specified keys
        to uppercase for consistency.
        """
        self._schema_definition = load_file(self._schema_definition_filepath)
        manifest_data = load_file(self._manifest_definition_filepath)
        self._manifest_definition = convert_specific_keys_to_uppercase(
            manifest_data, self._manifest_file_keys_to_uppercase
        )

    def _validate_sso_manifest_file(self) -> None:
        """
        Validate the SSO manifest file against its JSON schema.

        Raises:
            jsonschema.ValidationError: If the manifest does not conform
            to the specified JSON schema.
        """
        try:
            jsonschema.validate(
                instance=self._manifest_definition, schema=self._schema_definition
            )
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Validation error: {e.message}")

    def _generate_excluded_targets_lists(self) -> None:
        """
        Generate lists of excluded targets from the manifest file.

        Populates exclusion lists for different target types based on
        the 'ignore' section of the manifest file.
        """
        target_map = {
            OU_TARGET_TYPE_LABEL: self._excluded_ou_names,
            ACCOUNT_TARGET_TYPE_LABEL: self._excluded_account_names,
            USER_PRINCIPAL_TYPE_LABEL: self._excluded_sso_user_names,
            GROUP_PRINCIPAL_TYPE_LABEL: self._excluded_sso_group_names,
            PERMISSION_SET_TYPE_LABEL: self._excluded_permission_set_names,
        }

        for item in self._manifest_definition.get("ignore", []):
            target_list = target_map.get(item["target_type"])
            target_list.extend(item["target_names"])

    @property
    def rbac_rules(self) -> list:
        """
        Retrieve the RBAC (Role-Based Access Control) rules from the manifest.

        Returns:
            list: A list of RBAC rules defined in the manifest file.
        """
        return self._manifest_definition.get("rbac_rules", [])

    @property
    def excluded_ou_names(self) -> list[str]:
        """
        Get the list of excluded organizational unit names.

        Returns:
            list[str]: Names of organizational units to be excluded.
        """
        return self._excluded_ou_names

    @property
    def excluded_account_names(self) -> list[str]:
        """
        Get the list of excluded account names.

        Returns:
            list[str]: Names of accounts to be excluded.
        """
        return self._excluded_account_names

    @property
    def excluded_sso_user_names(self) -> list[str]:
        """
        Get the list of excluded SSO user names.

        Returns:
            list[str]: Names of SSO users to be excluded.
        """
        return self._excluded_sso_user_names

    @property
    def excluded_sso_group_names(self) -> list[str]:
        """
        Get the list of excluded SSO group names.

        Returns:
            list[str]: Names of SSO groups to be excluded.
        """
        return self._excluded_sso_group_names

    @property
    def excluded_permission_set_names(self) -> list[str]:
        """
        Get the list of excluded permission set names.

        Returns:
            list[str]: Names of permission sets to be excluded.
        """
        return self._excluded_permission_set_names
