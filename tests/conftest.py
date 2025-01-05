"""
This module provides fixtures and helper functions for testing AWS Organizations,
Identity Store, and SSO Admin services using the moto library and pytest framework.

The module includes:
- Helper functions to create and delete AWS Organizational Units (OUs) and accounts.
- Fixtures to set up and tear down AWS environment variables.
- Fixtures to mock AWS clients for Organizations, Identity Store, and SSO Admin services.
- A fixture to set up the AWS environment, including OUs, accounts, Identity Center users,
  groups, and permission sets.
"""

################################################
#                    Imports                   #
################################################

import os
import json
from typing import Optional

import moto
import boto3
import pytest

################################################
#                    Globals                   #
################################################

MONKEYPATCH = pytest.MonkeyPatch()

################################################
#               Helper functions               #
################################################


def create_aws_ous_accounts(
    orgs_client: boto3.client, aws_organization_definitions: list[dict], root_ou_id: str, parent_ou_id: str = "", account_name_id_map: Optional[dict] = None, ou_accounts_map: Optional[dict] = None, parent_ou_name: str = "root"
) -> None:
    """
    Fixture helper function to setup AWS mock organizations:
        1. Create AWS organization units (OUs)
        2. Create AWS accounts
        3. Move accounts under designated OUs

    Parameters:
    ----------
    - orgs_client: boto3.client
        AWS Organizations client.
    - aws_organization_definitions: list[dict]
        List of dictionaries defining AWS organizational structure.
    - root_ou_id: str
        Root organizational unit ID.
    - parent_ou_id: str, optional
        Parent organizational unit ID for nested setup.
    - account_name_id_map: dict, optional
        Dictionary to keep track of account names and their IDs.
    - ou_accounts_map: dict, optional
        Dictionary to keep track of OUs and their accounts.
    - parent_ou_name: str, optional
        Name of the parent OU for nested setup.
    """
    if account_name_id_map is None:
        account_name_id_map = {}

    if ou_accounts_map is None:
        ou_accounts_map = {}

    for organization_resource in aws_organization_definitions:
        if organization_resource["type"] == "ORGANIZATIONAL_UNIT":
            # Create OU
            nested_ou_id = orgs_client.create_organizational_unit(
                ParentId=parent_ou_id if parent_ou_id else root_ou_id,
                Name=organization_resource["name"],
            )[
                "OrganizationalUnit"
            ]["Id"]

            # Recursively setup OU
            if organization_resource.get("children"):
                create_aws_ous_accounts(orgs_client, organization_resource["children"], root_ou_id, nested_ou_id, account_name_id_map, ou_accounts_map, organization_resource["name"])

        elif organization_resource["type"] == "ACCOUNT":
            # Create account
            account_id = orgs_client.create_account(
                Email=f"{organization_resource['name']}@testing.com",
                AccountName=organization_resource["name"],
            )[
                "CreateAccountStatus"
            ]["AccountId"]

            # Move account to OU
            orgs_client.move_account(
                AccountId=account_id,
                SourceParentId=root_ou_id,
                DestinationParentId=parent_ou_id,
            )

            # Update the account_name_id_map with the new account
            account_name_id_map[organization_resource["name"]] = account_id

            # Update the ou_accounts_map with the new account under the correct OU
            if parent_ou_name not in ou_accounts_map:
                ou_accounts_map[parent_ou_name] = []

            ou_accounts_map[parent_ou_name].append({"Id": account_id, "Name": organization_resource["name"]})

    return account_name_id_map, ou_accounts_map


def delete_aws_ous_accounts(orgs_client: boto3.client, root_ou_id: str, parent_ou_id: str = "") -> None:
    """
    Recursively delete AWS accounts from nested organizational units (OUs).

    Parameters:
    ----------

    - orgs_client: boto3.client
        AWS Organizations client.
    - root_ou_id: str
        Root organizational unit ID.
    - parent_ou_id: str, optional
        Parent organizational unit ID for nested deletion.
    """

    # Function to delete accounts in the current OU
    def delete_accounts_in_ou(ou_id: str) -> None:
        accounts_to_delete = orgs_client.list_accounts_for_parent(ParentId=ou_id)["Accounts"]
        for account in accounts_to_delete:
            orgs_client.remove_account_from_organization(AccountId=account["Id"])

    # Function to recursively delete accounts in child OUs
    def delete_accounts_in_child_ous(parent_id: str) -> None:
        child_ous_paginator = orgs_client.get_paginator("list_children")
        for page in child_ous_paginator.paginate(ParentId=parent_id, ChildType="ORGANIZATIONAL_UNIT"):
            for child in page.get("Children", []):
                delete_accounts_in_ou(child["Id"])
                delete_accounts_in_child_ous(child["Id"])

    # Delete accounts in the root or specified parent OU
    if parent_ou_id:
        delete_accounts_in_ou(parent_ou_id)
        delete_accounts_in_child_ous(parent_ou_id)
    else:
        delete_accounts_in_ou(root_ou_id)
        delete_accounts_in_child_ous(root_ou_id)


################################################
#         Fixtures - AWS Env & Env Vars        #
################################################


@pytest.fixture(scope="session")
def setup_env_vars() -> None:
    """
    Fixture to set environment variables using MonkeyPatch for session scope.
    """
    MONKEYPATCH.setenv("AWS_SESSION_TOKEN", "test")
    MONKEYPATCH.setenv("AWS_ACCESS_KEY_ID", "test")
    MONKEYPATCH.setenv("AWS_SECRET_ACCESS_KEY", "test")
    MONKEYPATCH.setenv("AWS_DEFAULT_REGION", "us-east-1")
    yield


@pytest.fixture(scope="session")
def organizations_client(setup_env_vars: pytest.fixture) -> boto3.client:
    """
    Fixture to mock AWS Organizations client using moto for session scope.

    Returns:
    -------
    - boto3.client: Mocked AWS Organizations client.
    """
    with moto.mock_aws():
        yield boto3.client("organizations")


@pytest.fixture(scope="session")
def identity_store_client(setup_env_vars: pytest.fixture) -> boto3.client:
    """
    Fixture to mock AWS Identity Store client using moto for session scope.

    Returns:
    -------
    - boto3.client: Mocked AWS Identity Store client.
    """
    with moto.mock_aws():
        yield boto3.client("identitystore")


@pytest.fixture(scope="session")
def sso_admin_client(setup_env_vars: pytest.fixture) -> boto3.client:
    """
    Fixture to mock AWS SSO Admin client using moto for session scope.

    Returns:
    -------
    - boto3.client: Mocked AWS SSO Admin client.
    """
    with moto.mock_aws():
        yield boto3.client("sso-admin")


################################################
#         Fixtures - Local Unit Testing        #
################################################


@pytest.fixture(scope="session")
def setup_mock_aws_environment(
    request: str,
    organizations_client: boto3.client,  # pylint: disable=W0621
    identity_store_client: boto3.client,  # pylint: disable=W0621
    sso_admin_client: boto3.client,  # pylint: disable=W0621
) -> dict:
    """
    Fixture to setup AWS environment:
        1. Create AWS organization
        2. Setup AWS mock organizations with OUs and accounts
        3. Setup AWS Identity Center with users, groups, and permission sets

    Parameters:
    ----------
    - request: str
        Parameter from pytest marker or fixture definition.
    - organizations_client: boto3.client
        AWS Organizations client.
    - identity_store_client: boto3.client
        AWS Identity Store client.
    - sso_admin_client: boto3.client
        AWS SSO Admin client.

    Returns:
    -------
    - dict: Dictionary containing setup details:
        - root_ou_id: str
            Root organizational unit ID.
        - aws_organization_definitions: list[dict]
            List of dictionaries defining AWS organizational structure.
        - aws_sso_group_definitions: list
            List of dictionaries defining AWS SSO groups.
        - aws_sso_user_definitions: list
            List of dictionaries defining AWS SSO users.
        - aws_permission_set_definitions: list
            List of dictionaries defining AWS permission sets.
    """

    # Load JSON definitions
    cwd = os.path.dirname(os.path.realpath(__file__))
    organizations_map_path = os.path.join(cwd, "configs", "organizations", request.param)
    with open(organizations_map_path, "r", encoding="utf-8") as fp:
        aws_environment_details = json.load(fp)

    aws_organizations_definitions = aws_environment_details.get("aws_organizations", [])
    permission_set_definitions = aws_environment_details.get("permission_sets", [])
    sso_users = aws_environment_details.get("sso_users", [])
    sso_groups = aws_environment_details.get("sso_groups", [])

    root_ou_id = None
    created_sso_users = {}
    created_sso_groups = {}
    created_permission_sets = {}

    try:
        # Setup AWS organizations
        organizations_client.create_organization()
        root_ou_id = organizations_client.list_roots()["Roots"][0]["Id"]
        account_name_id_map, ou_accounts_map = create_aws_ous_accounts(
            orgs_client=organizations_client,
            aws_organization_definitions=aws_organizations_definitions,
            root_ou_id=root_ou_id,
        )

        # Setup AWS Identity center
        identity_store_instance = sso_admin_client.list_instances()["Instances"][0]
        for user in sso_users:
            user_details = identity_store_client.create_user(
                IdentityStoreId=identity_store_instance["IdentityStoreId"],
                UserName=user["username"],
                DisplayName=user["name"]["Formatted"],
                Name=user["name"],
                Emails=user["email"],
            )
            created_sso_users[user["username"]] = user_details["UserId"]

        for group in sso_groups:
            group_details = identity_store_client.create_group(
                IdentityStoreId=identity_store_instance["IdentityStoreId"],
                DisplayName=group["name"],
                Description=group["description"],
            )
            created_sso_groups[group["name"]] = group_details["GroupId"]

        for permission_set in permission_set_definitions:
            permission_set_details = sso_admin_client.create_permission_set(
                InstanceArn=identity_store_instance["InstanceArn"],
                Name=permission_set["name"],
                Description=permission_set["description"],
            )["PermissionSet"]
            created_permission_sets[permission_set["name"]] = permission_set_details["PermissionSetArn"]

        yield {
            "identity_store_arn": identity_store_instance["InstanceArn"],
            "sso_group_name_id_map": created_sso_groups,
            "sso_username_id_map": created_sso_users,
            "sso_permission_set_name_id_map": created_permission_sets,
            "account_name_id_map": account_name_id_map,
            "ou_accounts_map": ou_accounts_map,
        }

    finally:
        # Teardown logic
        # Remove AWS accounts from organization
        delete_aws_ous_accounts(orgs_client=organizations_client, root_ou_id=root_ou_id)

        # Delete AWS resources or undo changes as needed
        organizations_client.delete_organization(OrganizationId=root_ou_id)

        # Delete SSO users
        for user_id in created_sso_users.values():
            identity_store_client.delete_user(IdentityStoreId=identity_store_instance["IdentityStoreId"], UserId=user_id)

        # Delete SSO groups
        for group_id in created_sso_groups.values():
            identity_store_client.delete_group(IdentityStoreId=identity_store_instance["IdentityStoreId"], GroupId=group_id)

        # Delete permission sets
        for permission_set_arn in created_permission_sets.values():
            sso_admin_client.delete_permission_set(InstanceArn=identity_store_instance["InstanceArn"], PermissionSetArn=permission_set_arn)


################################################
#      Fixtures - Live Integration Testing     #
################################################


@pytest.fixture(scope="session")
def setup_live_aws_environment(
    request: str,
) -> dict:
    """
    Fixture to setup AWS environment:
        1. Create AWS organization
        2. Setup AWS mock organizations with OUs and accounts
        3. Setup AWS Identity Center with users, groups, and permission sets

    Parameters:
    ----------
    - request: str
        Parameter from pytest marker or fixture definition.
    - organizations_client: boto3.client
        AWS Organizations client.
    - identity_store_client: boto3.client
        AWS Identity Store client.
    """

    created_sso_users = {}
    created_sso_groups = {}
    created_permission_sets = {}

    try:
        # Set boto3 clients
        sso_admin_client = boto3.client("sso-admin")
        identity_store_client = boto3.client("identitystore")

        # Set environment variables
        identity_store_instance = sso_admin_client.list_instances()["Instances"][0]
        identity_store_instance["InstanceArn"] = identity_store_instance["InstanceArn"]
        identity_store_instance["IdentityStoreId"] = identity_store_instance["IdentityStoreId"]

        # Load JSON definitions
        organizations_map_filepath = request.param
        with open(organizations_map_filepath, "r", encoding="utf-8") as fp:
            aws_environment_details = json.load(fp)

        sso_users = aws_environment_details.get("sso_users", [])
        sso_groups = aws_environment_details.get("sso_groups", [])
        permission_set_definitions = aws_environment_details.get("permission_sets", [])

        # Setup AWS Identity center
        for user in sso_users:
            user_details = identity_store_client.create_user(
                IdentityStoreId=identity_store_instance["IdentityStoreId"],
                UserName=user["username"],
                DisplayName=user["name"]["Formatted"],
                Name=user["name"],
                Emails=user["email"],
            )
            created_sso_users[user["username"]] = user_details["UserId"]

        for group in sso_groups:
            group_details = identity_store_client.create_group(
                IdentityStoreId=identity_store_instance["IdentityStoreId"],
                DisplayName=group["name"],
                Description=group["description"],
            )
            created_sso_groups[group["name"]] = group_details["GroupId"]

        for permission_set in permission_set_definitions:
            permission_set_details = sso_admin_client.create_permission_set(
                InstanceArn=identity_store_instance["InstanceArn"],
                Name=permission_set["name"],
                Description=permission_set["description"],
            )["PermissionSet"]
            created_permission_sets[permission_set["name"]] = permission_set_details["PermissionSetArn"]

        yield {
            "sso_group_name_id_map": created_sso_groups,
            "sso_username_id_map": created_sso_users,
            "sso_permission_set_name_id_map": created_permission_sets,
        }

    finally:
        for user_id in created_sso_users.values():
            identity_store_client.delete_user(IdentityStoreId=identity_store_instance["IdentityStoreId"], UserId=user_id)

        for group_id in created_sso_groups.values():
            identity_store_client.delete_group(IdentityStoreId=identity_store_instance["IdentityStoreId"], GroupId=group_id)

        for permission_set_arn in created_permission_sets.values():
            sso_admin_client.delete_permission_set(InstanceArn=identity_store_instance["InstanceArn"], PermissionSetArn=permission_set_arn)
