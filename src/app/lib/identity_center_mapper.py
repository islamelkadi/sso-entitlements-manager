"""
Module to interact with the AWS IAM Identity Store service.
"""

import boto3


class AwsIdentityCentre:
    """
    A class to interact with AWS IAM Identity Store service.

    Attributes:
    -----------
    _identity_store_id: str
        The identity store ID.
    _identity_store_arn: str
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

    Methods:
    --------
    __init__(identity_store_id: str, identity_store_arn: str) -> None:
        Initializes the AwsIdentityCentre instance with the identity store ID and ARN.
    _map_sso_groups() -> None:
        Lists all groups in the identity store and maps DisplayName to GroupId.
    _map_sso_users() -> None:
        Lists all users in the identity store and maps UserName to UserId.
    _map_permission_sets() -> None:
        Lists all permission sets and maps Name to PermissionSetArn.
    """

    def __init__(self, identity_store_id: str, identity_store_arn: str) -> None:
        """
        Initializes the AwsIdentityCentre instance with the identity store ID and ARN.

        Parameters:
        ----------
        identity_store_id: str
            The identity store ID.
        identity_store_arn: str
            The identity store ARN.

        Usage:
        ------
        aws_identity_centre = AwsIdentityCentre("identity_store_id", "identity_store_arn")
        """
        self._identity_store_id = identity_store_id
        self._identity_store_arn = identity_store_arn

        self._sso_admin_client = boto3.client("sso-admin")
        self._identity_store_client = boto3.client("identitystore")

        self.sso_users = {}
        self.sso_groups = {}
        self.permission_sets = {}

        self._map_sso_users()
        self._map_sso_groups()
        self._map_permission_sets()

    def _map_sso_groups(self) -> None:
        """
        Lists all groups in the identity store and maps DisplayName to GroupId.
        """
        groups_paginator = self._identity_store_client.get_paginator("list_groups")

        sso_groups_list = []
        for page in groups_paginator.paginate(IdentityStoreId=self._identity_store_id):
            sso_groups_list.extend(page["Groups"])

        for group in sso_groups_list:
            self.sso_groups[group["DisplayName"]] = group["GroupId"]

    def _map_sso_users(self) -> None:
        """
        Lists all users in the identity store and maps UserName to UserId.
        """
        sso_users_pagniator = self._identity_store_client.get_paginator("list_users")

        sso_users_list = []
        for page in sso_users_pagniator.paginate(
            IdentityStoreId=self._identity_store_id
        ):
            sso_users_list.extend(page["Users"])

        for user in sso_users_list:
            self.sso_users[user["UserName"]] = user["UserId"]

    def _map_permission_sets(self) -> None:
        """
        Lists all permission sets and maps Name to PermissionSetArn.
        """
        permission_sets_paginator = self._sso_admin_client.get_paginator(
            "list_permission_sets"
        )

        permission_sets = []
        for page in permission_sets_paginator.paginate(
            InstanceArn=self._identity_store_arn
        ):
            permission_sets.extend(page["PermissionSets"])

        described_permission_sets = []
        for permission_set in permission_sets:
            permission_set_info = self._sso_admin_client.describe_permission_set(
                InstanceArn=self._identity_store_arn, PermissionSetArn=permission_set
            )
            described_permission_sets.append(permission_set_info.get("PermissionSet"))

        for permission_set in described_permission_sets:
            self.permission_sets[permission_set["Name"]] = permission_set[
                "PermissionSetArn"
            ]
