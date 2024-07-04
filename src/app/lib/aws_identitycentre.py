"""
Module to interact with the AWS IAM Identity Store service
"""
import boto3
from .utils import convert_list_to_dict, convert_specific_keys_to_lowercase


class AwsIdentityCentre:


    def __init__(self, identity_store_id: str, identity_store_arn: str) -> None:
        """
        Default constructor method to initialize
        identity store variable and boto3 client.
        """

        # Set class instance vars
        self._identity_store_id = identity_store_id
        self._identity_store_arn = identity_store_arn

        # Set boto3 clients
        self._sso_admin_client = boto3.client("sso-admin")
        self._identity_store_client = boto3.client("identitystore")

        # Set paginators
        self._sso_users_paginator = self._identity_store_client.get_paginator("list_users")
        self._sso_groups_paginator = self._identity_store_client.get_paginator("list_groups")
        self._permission_sets_paginator = self._sso_admin_client.get_paginator("list_permission_sets")

        # Get Identity center entities
        self.sso_users = convert_specific_keys_to_lowercase(convert_list_to_dict(self._list_sso_users(), "DisplayName"))
        self.sso_groups = convert_specific_keys_to_lowercase(convert_list_to_dict(self._list_sso_groups(), "DisplayName"))
        self.permission_sets = convert_specific_keys_to_lowercase(convert_list_to_dict(self._list_permission_sets(), "Name"))

    def _list_sso_groups(self):
        aws_identitystore_groups_iterator = self._sso_groups_paginator.paginate(IdentityStoreId=self._identity_store_id)
        sso_groups = []
        for page in aws_identitystore_groups_iterator:
            sso_groups.extend(page["Groups"])
        return sso_groups


    def _list_sso_users(self):
        """
        Method to list all the users in the identity store.
        """
        aws_identitystore_users_iterator = self._sso_users_paginator.paginate(IdentityStoreId=self._identity_store_id)
        sso_users = []
        for page in aws_identitystore_users_iterator:
            sso_users.extend(page["Users"])
        return sso_users

    def _list_permission_sets(self):
        """
        Method to list permission sets and remove sensitive information.
        """
        aws_permission_sets_iterator = self._permission_sets_paginator.paginate(InstanceArn=self._identity_store_arn)
        permission_sets = []
        for page in aws_permission_sets_iterator:
            permission_sets.extend(page["PermissionSets"])
        
        described_permission_sets = []
        for x in permission_sets:
            permission_set_info = self._sso_admin_client.describe_permission_set(InstanceArn=self._identity_store_arn, PermissionSetArn=x)
            described_permission_sets.append(permission_set_info.get("PermissionSet"))
        
        return described_permission_sets

    def create_permission_set_assignment(self, permission_set_arn: str, principal_id: str, principal_type: str, target_id: str):
        return self._sso_admin_client.create_account_assignment(
            InstanceArn = self._identity_store_arn,
            PermissionSetArn = permission_set_arn,
            PrincipalId = principal_id,
            PrincipalType = principal_type.upper(),
            TargetId = target_id,
            TargetType = "AWS_ACCOUNT"
        ).get("AccountAssignmentCreationStatus")
