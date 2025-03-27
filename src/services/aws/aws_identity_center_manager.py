"""
AWS Identity Center Access Management Module

This module provides tools for comprehensive management of AWS Identity Center (SSO) 
access control and account assignments.

The module defines a class `IdentityCenterManager` that facilitates:
- Mapping SSO users, groups, and permission sets
- Generating and managing Role-Based Access Control (RBAC) assignments
- Tracking and resolving account access permissions across AWS accounts

Key Features:
- Dynamic mapping of SSO principals and permission sets
- Generation of account assignments based on manifest file rules
- Support for automatic or manual approval of access changes
- Detailed reporting of invalid assignments

Example:
    # Initialize the manager with Identity Store details
    sso_manager = IdentityCenterManager('arn:aws:sso:region:account-id:instance/d-instance-id', 'identity-store-id')
    
    # Set RBAC rules from a manifest file
    sso_manager.manifest_file_rbac_rules = [...]
    
    # Run access control resolver
    sso_manager.run_access_control_resolver()

Note:
    Requires appropriate AWS IAM permissions to manage 
    Identity Center access and assignments.
"""

import logging
import itertools
from typing import Optional

import boto3
from src.services.aws.utils import handle_aws_exceptions
from src.core.constants import (
    OU_TARGET_TYPE_LABEL,
    ACCOUNT_TARGET_TYPE_LABEL,
    GROUP_PRINCIPAL_TYPE_LABEL,
    USER_PRINCIPAL_TYPE_LABEL,
    SSO_ENTITLMENTS_APP_NAME,
)


class NoPermissionSetsFoundError(Exception):
    """Raised when no permission sets are available for assignment."""


class NoSSOPrincipalsFoundError(Exception):
    """Raised when no SSO groups or users are found for access assignment."""


class IdentityCenterManager:
    """
    Manages AWS Identity Center (SSO) account assignments and access control.

    This class provides comprehensive functionality to map and manage SSO groups,
    users, permission sets, and account assignments across AWS accounts and
    organizational units.

    Attributes:
        _identity_store_arn (str): The ARN of the Identity Store.
        _identity_store_id (str): The ID of the Identity Store.
        sso_users (dict[str, str]): Mapping of SSO usernames to their user IDs.
        sso_groups (dict[str, str]): Mapping of SSO group names to their group IDs.
        sso_permission_sets (dict[str, str]): Mapping of permission set names to their ARNs.
        manifest_file_exclusions (Optional[list]): List of exclusions from the manifest file.
        manifest_file_rbac_rules (list): List of RBAC (Role-Based Access Control) rules.
        ou_accounts_map (dict): Mapping of Organizational Units to their accounts.
        account_name_id_map (dict): Mapping of account names to their IDs.
        is_auto_approved (bool): Flag to indicate if assignments should be automatically approved.

    Properties:
        invalid_assignments_report (list):
            A list of invalid assignments across different resource types
            (OUs, accounts, groups, users, and permission sets).
    """

    def __init__(self, identity_store_arn: str, identity_store_id: str) -> None:
        """
        Initialize the AWS Identity Center manager and set up SSO environment mapping.

        Args:
            identity_store_arn (str): The Amazon Resource Name (ARN) of the Identity Store.
            identity_store_id (str): The unique identifier for the Identity Store.

        Note:
            This method automatically maps the SSO environment and lists current
            account assignments during instantiation.
        """
        self._identity_store_arn = identity_store_arn
        self._identity_store_id = identity_store_id

        self.sso_users: dict[str, str] = {}
        self.sso_groups: dict[str, str] = {}
        self.sso_permission_sets: dict[str, str] = {}

        # Settable input attributes
        self.manifest_file_exclusions = None
        self.manifest_file_rbac_rules: list = []

        self.ou_accounts_map = {}
        self.account_name_id_map = {}
        self.is_auto_approved: bool = False

        # Define boto3 clients
        self._sso_admin_client = boto3.client("sso-admin")
        self._identity_store_client = boto3.client("identitystore")

        # Define AWS client API paginators
        self._list_groups_paginator = self._identity_store_client.get_paginator(
            "list_groups"
        )
        self._list_sso_users_pagniator = self._identity_store_client.get_paginator(
            "list_users"
        )
        self._list_permission_sets_paginator = self._sso_admin_client.get_paginator(
            "list_permission_sets"
        )

        # Define assignment variables
        self._local_account_assignments: list = []
        self._current_account_assignments: list = []

        self.assignments_to_create: list = []
        self.assignments_to_delete: list = []

        # Define invalid report variables
        self._invalid_manifest_file_ou_names: list = []
        self._invalid_manifest_file_account_names: list = []
        self._invalid_manifest_file_group_names: list = []
        self._invalid_manifest_file_user_names: list = []
        self._invalid_manifest_file_permission_sets: list = []

        # Define logger
        self._logger: logging.Logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)

        # Setup workflow
        self._map_sso_environment()
        self._list_current_account_assignments()

    @handle_aws_exceptions()
    def _map_sso_environment(self) -> None:
        """
        Maps the current SSO environment by populating SSO resources.

        This method comprehensively maps:
        - SSO Groups
        - SSO Users
        - SSO Permission Sets

        Populates:
        - self.sso_groups
        - self.sso_users
        - self.sso_permission_sets

        Raises:
            Exception: If no SSO groups, users, or permission sets are found.

        Note:
            Uses AWS Organizations API pagination to handle large numbers
            of groups, users, and permission sets.
        """
        # SSO Groups
        self._logger.info("Mapping SSO groups")
        sso_groups_pages = self._list_groups_paginator.paginate(
            IdentityStoreId=self._identity_store_id
        )
        for page in sso_groups_pages:
            for group in page.get("Groups", []):
                self.sso_groups[group["DisplayName"]] = group["GroupId"]

        # SSO Users
        self._logger.info("Mapping SSO users")
        sso_users_pages = self._list_sso_users_pagniator.paginate(
            IdentityStoreId=self._identity_store_id
        )
        for page in sso_users_pages:
            for user in page.get("Users", []):
                self.sso_users[user["UserName"]] = user["UserId"]

        if not (self.sso_groups and self.sso_users):
            self._logger.error(
                "No SSO groups or users principals found to assign access"
            )
            raise NoSSOPrincipalsFoundError(
                "No SSO groups or users principals found to assign access"
            )

        # SSO Permission Sets
        self._logger.info("Mapping SSO permission sets")
        permission_sets_pages = self._list_permission_sets_paginator.paginate(
            InstanceArn=self._identity_store_arn
        )
        for page in permission_sets_pages:
            for permission_set in page.get("PermissionSets", []):
                described_permission_set = (
                    self._sso_admin_client.describe_permission_set(
                        InstanceArn=self._identity_store_arn,
                        PermissionSetArn=permission_set,
                    )
                )
                permission_set = described_permission_set.get("PermissionSet")
                self.sso_permission_sets[permission_set["Name"]] = permission_set[
                    "PermissionSetArn"
                ]

        if not self.sso_permission_sets:
            self._logger.error(
                "No permission sets found to assign to groups or users principals"
            )
            raise NoPermissionSetsFoundError(
                "No permission sets found to assign to groups or users principals"
            )

    @handle_aws_exceptions()
    def _list_current_account_assignments(self) -> None:
        """
        Lists the current account assignments for principals in the identity store.

        This method:
        - Retrieves existing account assignments for users and groups
        - Populates _current_account_assignments list
        - Standardizes assignment dictionary format

        Note:
            Uses AWS SSO Admin API pagination to handle large numbers
            of account assignments.
        """
        principal_type_map = {"USER": self.sso_users, "GROUP": self.sso_groups}
        principal_assignments_paginator = self._sso_admin_client.get_paginator(
            "list_account_assignments_for_principal"
        )

        for principal_type, principals in principal_type_map.items():
            for principal_id in principals.values():
                assignments_iterator = principal_assignments_paginator.paginate(
                    PrincipalId=principal_id,
                    InstanceArn=self._identity_store_arn,
                    PrincipalType=principal_type,
                )
                for page in assignments_iterator:
                    self._current_account_assignments.extend(page["AccountAssignments"])

        for i, _ in enumerate(self._current_account_assignments):
            self._current_account_assignments[i][
                "InstanceArn"
            ] = self._identity_store_arn
            self._current_account_assignments[i]["TargetType"] = "AWS_ACCOUNT"
            self._current_account_assignments[i][
                "TargetId"
            ] = self._current_account_assignments[i].pop("AccountId")

    def _generate_rbac_assignments(self) -> None:
        """
        Generates Role-Based Access Control (RBAC) assignments.

        This method:
        - Validates RBAC rules against existing SSO resources
        - Creates a list of account assignments to be created or deleted
        - Populates assignments_to_create and assignments_to_delete lists
        - Tracks and logs invalid assignments

        Note:
            Performs comprehensive validation of:
            - Principals (users and groups)
            - Permission sets
            - Target accounts and organizational units
        """

        def validate_aws_resource(
            rule_number: int, resource_name: str, resource_type: str
        ) -> Optional[str]:
            """
            Validates AWS resources against predefined resource maps.

            Args:
                rule_number (int): The number of the current RBAC rule.
                resource_name (str): Name of the resource to validate.
                resource_type (str): Type of the resource (e.g., OU, account, group).

            Returns:
                Optional[str]: The validated resource ID or None if invalid.
            """
            resource_maps = {
                OU_TARGET_TYPE_LABEL: (
                    self.ou_accounts_map,
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
                    self.sso_permission_sets,
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

        def add_unique_assignment(
            target_id: int,
            principal_id: str,
            principal_type: str,
            permission_set_arn: str,
        ) -> None:
            """
            Adds a unique assignment to the list of resolved account assignments.

            Args:
                target_id (int): The target account ID for the assignment.
                principal_id (str): The ID of the principal (user or group).
                principal_type (str): The type of principal (USER or GROUP).
                permission_set_arn (str): The ARN of the permission set to assign.
            """
            assignment = {
                "TargetId": target_id,
                "TargetType": "AWS_ACCOUNT",
                "PrincipalId": principal_id,
                "PrincipalType": principal_type,
                "PermissionSetArn": permission_set_arn,
                "InstanceArn": self._identity_store_arn,
            }

            if assignment not in self._local_account_assignments:
                self._local_account_assignments.append(assignment)

        for i, rule in enumerate(self.manifest_file_rbac_rules):
            self._logger.info(rule)
            rule["rule_number"] = i
            rule["principal_id"] = validate_aws_resource(
                rule["rule_number"], rule["principal_name"], rule["principal_type"]
            )
            rule["permission_set_arn"] = validate_aws_resource(
                rule["rule_number"], rule["permission_set_name"], "permission_set"
            )
            if not (rule["principal_id"] and rule["permission_set_arn"]):
                self._logger.debug(
                    "Invalide Principal ID or Permission Set ARN provided for rule: %s. Continuing to next rule.",
                    rule["rule_number"],
                )
                continue

            for name in rule["target_names"]:
                is_valid_assignment_target = validate_aws_resource(
                    rule["rule_number"], name, rule["target_type"]
                )
                if is_valid_assignment_target:
                    if rule["target_type"] == OU_TARGET_TYPE_LABEL:
                        for child_ou_account in self.ou_accounts_map[name]:
                            add_unique_assignment(
                                child_ou_account["Id"],
                                rule["principal_id"],
                                rule["principal_type"],
                                rule["permission_set_arn"],
                            )
                    else:
                        account_id = self.account_name_id_map[name]
                        add_unique_assignment(
                            account_id,
                            rule["principal_id"],
                            rule["principal_type"],
                            rule["permission_set_arn"],
                        )

        self._logger.info("Creating itinerary of SSO account assignments to create")
        assignments_to_create = list(
            itertools.filterfalse(
                lambda i: i in self._current_account_assignments,
                self._local_account_assignments,
            )
        )
        for assignment in assignments_to_create:
            self.assignments_to_create.append(assignment)

        self._logger.warning("Creating itinerary of SSO account assignments to delete")
        assignments_to_delete = list(
            itertools.filterfalse(
                lambda i: i in self._local_account_assignments,
                self._current_account_assignments,
            )
        )
        for assignment in assignments_to_delete:
            self.assignments_to_delete.append(assignment)

    def _execute_rbac_assignments(self) -> None:
        """
        Executes the RBAC assignments by creating and deleting account assignments.

        This method:
        - Creates new account assignments from assignments_to_create list
        - Deletes obsolete account assignments from assignments_to_delete list

        Note:
            Actual assignment creation and deletion are performed using
            AWS SSO Admin API methods.
        """
        self._logger.info("Executing create itinerary of SSO account assignments")
        for assignment in self.assignments_to_create:
            self._sso_admin_client.create_account_assignment(**assignment)

        self._logger.warning("Creating delete itinerary of SSO account assignments")
        for assignment in self.assignments_to_delete:
            self._sso_admin_client.delete_account_assignment(**assignment)

    def run_access_control_resolver(self) -> None:
        """
        Runs the full access control resolver process.

        This method performs the following steps:
        1. Generates RBAC AWS account SSO assignments
        2. If auto-approval is enabled, executes the assignments

        Note:
            The is_auto_approved flag controls whether assignments are
            automatically applied or require manual intervention.
        """
        self._logger.info("Generating RBAC AWS account SSO assignments to process")
        self._generate_rbac_assignments()

        if self.is_auto_approved:
            self._logger.warning("Running in auto-approved mode")
            self._logger.info("Executing RBAC assignments")
            self._execute_rbac_assignments()

    @property
    def invalid_assignments_report(self) -> list:
        """
        Generates a report of invalid assignments.

        Returns:
            list: A compiled list of invalid entries across different resource types
            (OUs, accounts, groups, users, and permission sets).

        Note:
            This property aggregates all invalid resource mappings encountered
            during the RBAC assignment generation process.
        """
        self._logger.info("Generate invalid AWS account SSO assignments")
        return (
            self._invalid_manifest_file_ou_names
            + self._invalid_manifest_file_account_names
            + self._invalid_manifest_file_group_names
            + self._invalid_manifest_file_user_names
            + self._invalid_manifest_file_permission_sets
        )
