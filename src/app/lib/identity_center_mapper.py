"""
Module to interact with the AWS IAM Identity Store service.
"""

import boto3
from .utils import convert_list_to_dict, convert_specific_keys_to_uppercase


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
    _sso_users_paginator: boto3.paginate.Paginator
        Paginator for listing SSO users.
    _sso_groups_paginator: boto3.paginate.Paginator
        Paginator for listing SSO groups.
    _permission_sets_paginator: boto3.paginate.Paginator
        Paginator for listing permission sets.
    sso_users: dict
        Dictionary of SSO users.
    sso_groups: dict
        Dictionary of SSO groups.
    permission_sets: dict
        Dictionary of permission sets.

    Methods:
    --------
    __init__(identity_store_id: str, identity_store_arn: str) -> None:
        Initializes the AwsIdentityCentre instance with the identity store ID and ARN.
    _list_sso_groups() -> list:
        Lists all groups in the identity store.
    _list_sso_users() -> list:
        Lists all users in the identity store.
    _list_permission_sets() -> list:
        Lists all permission sets and removes sensitive information.
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

        self._sso_users_paginator = self._identity_store_client.get_paginator(
            "list_users"
        )
        self._sso_groups_paginator = self._identity_store_client.get_paginator(
            "list_groups"
        )
        self._permission_sets_paginator = self._sso_admin_client.get_paginator(
            "list_permission_sets"
        )

        self.sso_users = convert_specific_keys_to_uppercase(
            convert_list_to_dict(self._list_sso_users(), "UserName")
        )
        self.sso_groups = convert_specific_keys_to_uppercase(
            convert_list_to_dict(self._list_sso_groups(), "DisplayName")
        )
        self.permission_sets = convert_specific_keys_to_uppercase(
            convert_list_to_dict(self._list_permission_sets(), "Name")
        )

    def _list_sso_groups(self) -> list:
        """
        Lists all groups in the identity store.

        Returns:
        -------
        list
            A list of SSO groups.

        Usage:
        ------
        sso_groups = self._list_sso_groups()
        """
        groups = []
        for page in self._sso_groups_paginator.paginate(
            IdentityStoreId=self._identity_store_id
        ):
            groups.extend(page["Groups"])
        return groups

    def _list_sso_users(self) -> list:
        """
        Lists all the users in the identity store.

        Returns:
        -------
        list
            A list of SSO users.

        Usage:
        ------
        sso_users = self._list_sso_users()
        """
        users = []
        for page in self._sso_users_paginator.paginate(
            IdentityStoreId=self._identity_store_id
        ):
            users.extend(page["Users"])
        return users

    def _list_permission_sets(self) -> list:
        """
        Lists all permission sets and removes sensitive information.

        Returns:
        -------
        list
            A list of described permission sets.

        Usage:
        ------
        permission_sets = self._list_permission_sets()
        """
        permission_sets = []
        for page in self._permission_sets_paginator.paginate(
            InstanceArn=self._identity_store_arn
        ):
            permission_sets.extend(page["PermissionSets"])

        described_permission_sets = []
        for permission_set in permission_sets:
            permission_set_info = self._sso_admin_client.describe_permission_set(
                InstanceArn=self._identity_store_arn, PermissionSetArn=permission_set
            )
            described_permission_sets.append(permission_set_info.get("PermissionSet"))

        return described_permission_sets
