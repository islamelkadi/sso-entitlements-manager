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

    def __init__(self) -> None:
        """
        Initializes AwsAccessControlResolver with the provided identity store ARN.

        Args:
            identity_store_arn (str): The ARN of the AWS Identity Store.
        """
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
        self._logger.info("Retrieving IAM Identity Center tenant information")
        iam_identity_center_details = self._sso_admin_client.list_instances()["Instances"][0]
        identity_store_id = iam_identity_center_details["IdentityStoreId"]
        identity_store_arn = iam_identity_center_details["InstanceArn"]

        # SSO Groups
        self._logger.info("Mapping SSO groups")
        sso_groups_pages = self._list_groups_paginator.paginate(IdentityStoreId=identity_store_id)
        for page in sso_groups_pages:
            for group in page.get("Groups", []):
                self._sso_groups[group["DisplayName"]] = group["GroupId"]

        # SSO Users
        self._logger.info("Mapping SSO users")
        sso_users_pages = self._list_sso_users_pagniator.paginate(IdentityStoreId=identity_store_id)
        for page in sso_users_pages:
            for user in page.get("Users", []):
                self._sso_users[user["UserName"]] = user["UserId"]

        # SSO Permission Sets
        self._logger.info("Mapping SSO permission sets")
        permission_sets_pages = self._list_permission_sets_paginator.paginate(InstanceArn=identity_store_arn)
        for page in permission_sets_pages:
            for permission_set in page.get("PermissionSets", []):
                described_permission_set = self._sso_admin_client.describe_permission_set(InstanceArn=identity_store_arn, PermissionSetArn=permission_set)
                permission_set = described_permission_set.get("PermissionSet")
                self._permission_sets[permission_set["Name"]] = permission_set["PermissionSetArn"]

    @property
    def sso_users(self) -> dict[str, str]:
        return self._sso_users

    @property
    def sso_groups(self) -> dict[str, str]:
        return self._sso_groups

    @property
    def permission_sets(self) -> dict[str, str]:
        return self._permission_sets
