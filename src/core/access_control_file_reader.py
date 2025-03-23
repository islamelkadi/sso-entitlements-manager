

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

    def __init__(self, manifest_definition_filepath, schema_definition_filepath) -> None:
        self._schema_definition_filepath: str = schema_definition_filepath
        self._manifest_definition_filepath: str = manifest_definition_filepath
        self._excluded_ou_names: list[str] = []
        self._excluded_account_names: list[str] = []
        self._excluded_sso_user_names: list[str] = []
        self._excluded_sso_group_names: list[str] = []
        self._excluded_permission_set_names: list[str] = []
        self._manifest_file_keys_to_uppercase: list[str] = [
            "principal_type",
            "target_type",
            "exclude_target_type",
        ]

        self._load_sso_manifest_file()
        self._validate_sso_manifest_file()
        self._generate_excluded_targets_lists()

    def _load_sso_manifest_file(self) -> None:
        self._schema_definition = load_file(self._schema_definition_filepath)
        manifest_data = load_file(self._manifest_definition_filepath)
        self._manifest_definition = convert_specific_keys_to_uppercase(manifest_data, self._manifest_file_keys_to_uppercase)

    def _validate_sso_manifest_file(self) -> None:
        try:
            jsonschema.validate(instance=self._manifest_definition, schema=self._schema_definition)
        except jsonschema.ValidationError as e:
            raise jsonschema.ValidationError(f"Validation error: {e.message}")

    def _generate_excluded_targets_lists(self) -> None:
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
        return self._manifest_definition.get("rbac_rules", [])

    @property
    def excluded_ou_names(self) -> dict[str, list[str]]:
        return self._excluded_ou_names

    @property
    def excluded_account_names(self) -> dict[str, list[str]]:
        return self._excluded_account_names

    @property
    def excluded_sso_user_names(self) -> dict[str, list[str]]:
        return self._excluded_sso_user_names

    @property
    def excluded_sso_group_names(self) -> dict[str, list[str]]:
        return self._excluded_sso_group_names

    @property
    def excluded_permission_set_names(self) -> dict[str, list[str]]:
        return self._excluded_permission_set_names
