"""
Module for resolving AWS resources and creating access
control assignments based on ingested customer manifest file.
"""
import logging
import boto3
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.services.aws.utils import handle_aws_exceptions


class SsoAdminMapper:
    """
    Class for resolving AWS resources and creating RBAC (Role-Based Access Control)
    assignments based on a manifest file.
    """

    def __init__(self, identity_store_arn: str, identity_store_id: str) -> None:
        """
        Initializes AwsAccessControlResolver with the provided identity store ARN.

        Args:
            identity_store_arn (str): The ARN of the AWS Identity Store.
        """

        self._identity_store_arn = identity_store_arn
        self._identity_store_id = identity_store_id

        self._sso_users: dict[str, str] = {}
        self._sso_groups: dict[str, str] = {}
        self._permission_sets: dict[str, str] = {}

        self._sso_admin_client = boto3.client("sso-admin")
        self._identity_store_client = boto3.client("identitystore")

        self._list_groups_paginator = self._identity_store_client.get_paginator("list_groups")
        self._list_sso_users_pagniator = self._identity_store_client.get_paginator("list_users")
        self._list_permission_sets_paginator = self._sso_admin_client.get_paginator("list_permission_sets")

        self._logger: logging.Logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
        self._map_sso_environment()

    @handle_aws_exceptions()
    def _map_sso_environment(self) -> None:

        # SSO Groups
        self._logger.info("Mapping SSO groups")
        sso_groups_pages = self._list_groups_paginator.paginate(IdentityStoreId=self._identity_store_id)
        for page in sso_groups_pages:
            for group in page.get("Groups", []):
                self._sso_groups[group["DisplayName"]] = group["GroupId"]

        # SSO Users
        self._logger.info("Mapping SSO users")
        sso_users_pages = self._list_sso_users_pagniator.paginate(IdentityStoreId=self._identity_store_id)
        for page in sso_users_pages:
            for user in page.get("Users", []):
                self._sso_users[user["UserName"]] = user["UserId"]

        if not (self._sso_groups and self._sso_users):
            raise Exception("No SSO groups or users principals found to assign access")

        # SSO Permission Sets
        self._logger.info("Mapping SSO permission sets")
        permission_sets_pages = self._list_permission_sets_paginator.paginate(InstanceArn=self._identity_store_arn)
        for page in permission_sets_pages:
            for permission_set in page.get("PermissionSets", []):
                described_permission_set = self._sso_admin_client.describe_permission_set(InstanceArn=self._identity_store_arn, PermissionSetArn=permission_set)
                permission_set = described_permission_set.get("PermissionSet")
                self._permission_sets[permission_set["Name"]] = permission_set["PermissionSetArn"]

        if not self._permission_sets:
            raise Exception("No permission sets found to assign to groups or users principals")

    @property
    def sso_users_name_id_map(self) -> dict[str, str]:
        return self._sso_users

    @property
    def sso_groups_name_id_map(self) -> dict[str, str]:
        return self._sso_groups

    @property
    def permission_sets_name_id_map(self) -> dict[str, str]:
        return self._permission_sets
