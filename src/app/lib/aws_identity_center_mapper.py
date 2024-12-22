"""
Module to interact with the AWS IAM Identity Store service.

This module provides a class to facilitate interactions with AWS IAM Identity Store,
including mapping SSO users, groups, and permission sets.

Classes:
--------
AwsIdentityCenterMapper
    A class to interact with AWS IAM Identity Store service.

    Attributes:
    -----------
    identity_store_id: str
        The identity store ID.
    identity_store_arn: str
        The identity store ARN.
    _sso_admin_client: boto3.client
        The boto3 client for AWS SSO Admin.
    _identity_store_client: boto3.client
        The boto3 client for AWS Identity Store.
    sso_users: dict
        Dictionary mapping UserName to UserId for SSO users.
    sso_groups: dict
        Dictionary mapping DisplayName to GroupId for SSO groups.
    permission_sets: dict
        Dictionary mapping Name to PermissionSetArn for permission sets.
    exclude_sso_users: list
        List of SSO user names to be excluded.
    exclude_sso_groups: list
        List of SSO group display names to be excluded.
    exclude_permission_sets: list
        List of permission set names to be excluded.

    Methods:
    --------
    __init__(identity_store_id: str, identity_store_arn: str) -> None
        Initializes the AwsIdentityCenterMapper instance with the identity store ID and ARN.
    _map_sso_groups() -> None
        Lists all groups in the identity store and maps DisplayName to GroupId.
    _map_sso_users() -> None
        Lists all users in the identity store and maps UserName to UserId.
    _map_permission_sets() -> None
        Lists all permission sets and maps Name to PermissionSetArn.
    run_identity_center_mapper() -> None
        Runs all mapping methods to update SSO users, groups, and permission sets.
"""
import boto3

class AwsIdentityCenterMapper:
    """
    A class to interact with AWS IAM Identity Store service.

    Attributes:
    -----------
    identity_store_id: str
        The identity store ID.
    identity_store_arn: str
        The identity store ARN.
    _sso_admin_client: boto3.client
        The boto3 client for AWS SSO Admin.
    _identity_store_client: boto3.client
        The boto3 client for AWS Identity Store.
    sso_users: dict
        Dictionary mapping UserName to UserId for SSO users.
    sso_groups: dict
        Dictionary mapping DisplayName to GroupId for SSO groups.
    permission_sets: dict
        Dictionary mapping Name to PermissionSetArn for permission sets.
    exclude_sso_users: list
        List of SSO user names to be excluded.
    exclude_sso_groups: list
        List of SSO group display names to be excluded.
    exclude_permission_sets: list
        List of permission set names to be excluded.

    Methods:
    --------
    __init__(identity_store_id: str, identity_store_arn: str) -> None
        Initializes the AwsIdentityCenterMapper instance with the identity store ID and ARN.
    _map_sso_groups() -> None
        Lists all groups in the identity store and maps DisplayName to GroupId.
    _map_sso_users() -> None
        Lists all users in the identity store and maps UserName to UserId.
    _map_permission_sets() -> None
        Lists all permission sets and maps Name to PermissionSetArn.
    run_identity_center_mapper() -> None
        Runs all mapping methods to update SSO users, groups, and permission sets.
    """

    def __init__(self) -> None:
        """
        Initializes the AwsIdentityCenterMapper instance with the identity store ID and ARN.

        Parameters:
        ----------
        identity_store_id: str
            The identity store ID.
        identity_store_arn: str
            The identity store ARN.

        Usage:
        ------
        aws_identity_centre = AwsIdentityCenterMapper("identity_store_id", "identity_store_arn")
        """

        self.exclude_sso_users = []
        self.exclude_sso_groups = []
        self.exclude_permission_sets = []

        self._sso_admin_client = boto3.client("sso-admin")
        self._identity_store_client = boto3.client("identitystore")

    def _describe_identity_center_instance(self) -> None:
        iam_identity_center_details = self._sso_admin_client.list_instances()["Instances"][0]
        self.identity_store_id = iam_identity_center_details["IdentityStoreId"]
        self.identity_store_arn = iam_identity_center_details["InstanceArn"]

    def _map_sso_groups(self) -> None:
        """
        Lists all groups in the identity store and maps DisplayName to GroupId.
        """
        current_sso_groups = []
        groups_paginator = self._identity_store_client.get_paginator("list_groups")
        for page in groups_paginator.paginate(IdentityStoreId=self.identity_store_id):
            current_sso_groups.extend(page["Groups"])

        self.sso_groups = {}
        for group in current_sso_groups:
            if group["DisplayName"] not in self.exclude_sso_groups:
                self.sso_groups[group["DisplayName"]] = group["GroupId"]

    def _map_sso_users(self) -> None:
        """
        Lists all users in the identity store and maps UserName to UserId.
        """
        current_sso_users = []
        sso_users_pagniator = self._identity_store_client.get_paginator("list_users")
        sso_users_pages = sso_users_pagniator.paginate(IdentityStoreId=self.identity_store_id)
        for page in sso_users_pages:
            current_sso_users.extend(page["Users"])

        self.sso_users = {}
        for user in current_sso_users:
            if user["UserName"] not in self.exclude_sso_users:
                self.sso_users[user["UserName"]] = user["UserId"]

    def _map_permission_sets(self) -> None:
        """
        Lists all permission sets and maps Name to PermissionSetArn.
        """
        current_permission_sets = []
        permission_sets_paginator = self._sso_admin_client.get_paginator("list_permission_sets")
        permission_sets_pages = permission_sets_paginator.paginate(InstanceArn=self.identity_store_arn)
        for page in permission_sets_pages:
            current_permission_sets.extend(page["PermissionSets"])

        described_current_permission_sets = []
        for permission_set in current_permission_sets:
            permission_set_info = self._sso_admin_client.describe_permission_set(InstanceArn=self.identity_store_arn, PermissionSetArn=permission_set)
            described_current_permission_sets.append(permission_set_info.get("PermissionSet"))

        self.permission_sets = {}
        for permission_set in described_current_permission_sets:
            if permission_set["Name"] not in self.exclude_permission_sets:
                self.permission_sets[permission_set["Name"]] = permission_set["PermissionSetArn"]

    def run_identity_center_mapper(self) -> None:
        """
        Runs all mapping methods to update SSO users, groups, and permission sets.
        """
        self._describe_identity_center_instance()
        self._map_sso_users()
        self._map_sso_groups()
        self._map_permission_sets()
