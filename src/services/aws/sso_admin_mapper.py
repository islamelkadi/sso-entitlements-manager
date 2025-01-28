"""
Module for resolving AWS resources and creating access
control assignments based on ingested customer manifest file.
"""
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import boto3
from src.core.constants import OU_TARGET_TYPE_LABEL, ACCOUNT_TARGET_TYPE_LABEL, USER_PRINCIPAL_TYPE_LABEL, GROUP_PRINCIPAL_TYPE_LABEL, SSO_ENTITLMENTS_APP_NAME
from .utils import handle_aws_exceptions

@dataclass(frozen=True)
class AccountAssignment:
    """
    Dataclass defining the schema for SSO account assignments
    """
    target_id: str
    principal_id: str
    principal_type: str  # "USER" or "GROUP"
    permission_set_arn: str
    instance_arn: str
    target_type: str = field(default="AWS_ACCOUNT")  # Always "AWS_ACCOUNT"


class SsoAdminManager:
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
        self.permission_sets: Dict[str,str] = {}
        self.sso_groups: Dict[str, str] = {}
        self.sso_users: Dict[str, str] = {}
        self._sso_admin_client: boto3.client = boto3.client("sso-admin")
        self._identity_store_client: boto3.client = boto3.client("identitystore")
        self._logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)

    @handle_aws_exceptions()
    def _describe_identity_center_instance(self) -> None:
        self._logger.info("Retrieving IAM Identity Center tenant information")
        iam_identity_center_details = self._sso_admin_client.list_instances()["Instances"][0]
        self.identity_store_id = iam_identity_center_details["IdentityStoreId"]
        self.identity_store_arn = iam_identity_center_details["InstanceArn"]

    @handle_aws_exceptions()
    def _map_sso_groups(self) -> None:
        """
        Lists all groups in the identity store and maps DisplayName to GroupId.
        """
        groups_paginator = self._identity_store_client.get_paginator("list_groups")
        for page in groups_paginator.paginate(IdentityStoreId=self.identity_store_id):
            for group in page.get("Groups", []):
                self.sso_groups[group["DisplayName"]] = group["GroupId"]

    @handle_aws_exceptions()
    def _map_sso_users(self) -> None:
        """
        Lists all users in the identity store and maps UserName to UserId.
        """
        sso_users_pagniator = self._identity_store_client.get_paginator("list_users")
        sso_users_pages = sso_users_pagniator.paginate(IdentityStoreId=self.identity_store_id)
        for page in sso_users_pages:
            for user in page.get("Users", []):
                self.sso_users[user["UserName"]] = user["UserId"]

    @handle_aws_exceptions()
    def _map_permission_sets(self) -> None:
        """
        Lists all permission sets and maps Name to PermissionSetArn.
        """
        permission_sets_paginator = self._sso_admin_client.get_paginator("list_permission_sets")
        permission_sets_pages = permission_sets_paginator.paginate(InstanceArn=self.identity_store_arn)
        for page in permission_sets_pages:
            for permission_set in page.get("PermissionSets", []):
                described_permission_set= self._sso_admin_client.describe_permission_set(InstanceArn=self.identity_store_arn, PermissionSetArn=permission_set)
                permission_set = described_permission_set.get("PermissionSet")
                self.permission_sets[permission_set["Name"]] = permission_set["PermissionSetArn"]
