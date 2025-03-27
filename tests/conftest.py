"""
AWS Organizations and Identity Center Test Fixtures Module

This module provides comprehensive testing utilities for AWS services using moto 
and pytest. It facilitates the creation of mock AWS environments, including:
- Organizational Units (OUs)
- Accounts
- Identity Center users and groups
- Permission sets

Key Features:
- Helper functions for creating and deleting AWS organizational structures
- Pytest fixtures for mocking AWS service clients
- Session-scoped environment setup and teardown
- Flexible configuration loading for test environments

Attributes:
    MONKEYPATCH (pytest.MonkeyPatch): Global MonkeyPatch instance for 
        environment variable manipulation.

Dependencies:
    - moto
    - boto3
    - pytest
"""

import os
import json
from typing import Optional

import moto
import boto3
import pytest

# Define constants
MONKEYPATCH = pytest.MonkeyPatch()


# Define helper functions
def create_aws_ous_accounts(
    orgs_client: boto3.client,
    aws_organization_definitions: list[dict],
    root_ou_id: str,
    parent_ou_id: str = "",
    account_name_id_map: Optional[dict] = None,
    ou_accounts_map: Optional[dict] = None,
    parent_ou_name: str = "root",
) -> tuple[dict, dict]:
    """
    Recursively create AWS Organizational Units (OUs) and accounts.

    This function performs the following tasks:
    1. Create organizational units based on the provided definitions
    2. Create accounts within those organizational units
    3. Move accounts to their designated organizational units
    4. Maintain mappings of account names to IDs and OU structure

    Args:
        orgs_client (boto3.client): AWS Organizations client for API calls.
        aws_organization_definitions (list[dict]): Hierarchical definition of
            organizational structure and accounts.
        root_ou_id (str): ID of the root organizational unit.
        parent_ou_id (str, optional): ID of the parent OU for nested creation.
            Defaults to empty string.
        account_name_id_map (dict, optional): Mapping of account names to their
            AWS account IDs. Defaults to None.
        ou_accounts_map (dict, optional): Mapping of OUs to their accounts.
            Defaults to None.
        parent_ou_name (str, optional): Name of the parent OU for nested creation.
            Defaults to "root".

    Returns:
        tuple[dict, dict]: A tuple containing:
            - Updated account name to ID mapping
            - Updated OU to accounts mapping
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
            )["OrganizationalUnit"]["Id"]

            # Recursively setup OU
            if organization_resource.get("children"):
                create_aws_ous_accounts(
                    orgs_client,
                    organization_resource["children"],
                    root_ou_id,
                    nested_ou_id,
                    account_name_id_map,
                    ou_accounts_map,
                    organization_resource["name"],
                )

        elif organization_resource["type"] == "ACCOUNT":
            # Create account
            account_id = orgs_client.create_account(
                Email=f"{organization_resource['name']}@testing.com",
                AccountName=organization_resource["name"],
            )["CreateAccountStatus"]["AccountId"]

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

            ou_accounts_map[parent_ou_name].append(
                {"Id": account_id, "Name": organization_resource["name"]}
            )

    return account_name_id_map, ou_accounts_map


def delete_aws_ous_accounts(
    orgs_client: boto3.client, root_ou_id: str, parent_ou_id: str = ""
) -> None:
    """
    Recursively delete AWS accounts from organizational units.

    This function traverses the AWS organization structure and removes
    accounts from specified organizational units, supporting nested
    organizational hierarchies.

    Args:
        orgs_client (boto3.client): AWS Organizations client for API calls.
        root_ou_id (str): ID of the root organizational unit.
        parent_ou_id (str, optional): ID of the parent OU for targeted deletion.
            Defaults to empty string.

    Notes:
        - Deletes accounts in the specified OU and its child OUs
        - Uses pagination to handle large numbers of accounts and OUs
    """

    # Function to delete accounts in the current OU
    def delete_accounts_in_ou(ou_id: str) -> None:
        accounts_to_delete = orgs_client.list_accounts_for_parent(ParentId=ou_id)[
            "Accounts"
        ]
        for account in accounts_to_delete:
            orgs_client.remove_account_from_organization(AccountId=account["Id"])

    # Function to recursively delete accounts in child OUs
    def delete_accounts_in_child_ous(parent_id: str) -> None:
        child_ous_paginator = orgs_client.get_paginator("list_children")
        for page in child_ous_paginator.paginate(
            ParentId=parent_id, ChildType="ORGANIZATIONAL_UNIT"
        ):
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


# Define fixtures
@pytest.fixture(scope="session")
def setup_env_vars() -> None:
    """
    Set up environment variables for AWS testing.

    This fixture uses MonkeyPatch to set mock AWS credentials and region
    for the entire test session, ensuring consistent test environment
    configuration.

    Env Vars Set:
    - AWS_SESSION_TOKEN: Mock session token
    - AWS_ACCESS_KEY_ID: Mock access key
    - AWS_SECRET_ACCESS_KEY: Mock secret access key
    - AWS_DEFAULT_REGION: Default testing region (us-east-1)
    """
    MONKEYPATCH.setenv("AWS_SESSION_TOKEN", "test")
    MONKEYPATCH.setenv("AWS_ACCESS_KEY_ID", "test")
    MONKEYPATCH.setenv("AWS_SECRET_ACCESS_KEY", "test")
    MONKEYPATCH.setenv("AWS_DEFAULT_REGION", "us-east-1")
    yield


@pytest.fixture(scope="session")
def organizations_client(setup_env_vars: pytest.fixture) -> boto3.client:
    """
    Create a mocked AWS Organizations client for testing.

    Returns a moto-mocked AWS Organizations client with session scope,
    allowing for simulated AWS Organizations API interactions without
    making actual AWS service calls.

    Returns:
        boto3.client: Mocked AWS Organizations client
    """
    with moto.mock_aws():
        yield boto3.client("organizations")


@pytest.fixture(scope="session")
def identity_store_client(setup_env_vars: pytest.fixture) -> boto3.client:
    """
    Create a mocked AWS Identity Store client for testing.

    Returns a moto-mocked AWS Identity Store client with session scope,
    allowing for simulated AWS Identity Store API interactions without
    making actual AWS service calls.

    Returns:
        boto3.client: Mocked AWS Identity Store client
    """
    with moto.mock_aws():
        yield boto3.client("identitystore")


@pytest.fixture(scope="session")
def sso_admin_client(setup_env_vars: pytest.fixture) -> boto3.client:
    """
    Create a mocked AWS SSO Admin client for testing.

    Returns a moto-mocked AWS SSO Admin client with session scope,
    allowing for simulated AWS SSO Admin API interactions without
    making actual AWS service calls.

    Returns:
        boto3.client: Mocked AWS SSO Admin client
    """
    with moto.mock_aws():
        yield boto3.client("sso-admin")


@pytest.fixture(scope="session")
def setup_mock_aws_environment(
    request: str,
    organizations_client: boto3.client,
    identity_store_client: boto3.client,
    sso_admin_client: boto3.client,
) -> dict:
    """
    Comprehensive fixture to set up a mock AWS testing environment.

    This fixture performs a complete setup of a mock AWS environment,
    including:
    1. Creating an AWS organization
    2. Setting up organizational units and accounts
    3. Creating Identity Center users, groups, and permission sets
    4. Managing environment variables and resource mappings

    Args:
        request (str): Pytest request object for parameterized configuration.
        organizations_client (boto3.client): AWS Organizations client.
        identity_store_client (boto3.client): AWS Identity Store client.
        sso_admin_client (boto3.client): AWS SSO Admin client.

    Returns:
        dict: A comprehensive dictionary containing:
            - root_ou_id: Root organizational unit ID
            - identity_store_arn: Identity Store instance ARN
            - identity_store_id: Identity Store instance ID
            - sso_group_name_id_map: Mapping of SSO group names to IDs
            - sso_username_id_map: Mapping of SSO usernames to IDs
            - sso_permission_set_name_id_map: Mapping of permission set names to ARNs
            - account_name_id_map: Mapping of account names to IDs
            - ou_accounts_map: Mapping of OUs to their accounts

    Notes:
        - Uses JSON configuration files to define environment structure
        - Automatically handles teardown of created resources
        - Sets relevant environment variables for further testing
    """
    # Load JSON definitions
    cwd = os.path.dirname(os.path.realpath(__file__))
    organizations_map_path = os.path.join(
        cwd, "configs", "organizations", request.param
    )
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
            created_permission_sets[permission_set["name"]] = permission_set_details[
                "PermissionSetArn"
            ]

        # SET ENV VARS
        MONKEYPATCH.setenv("ROOT_OU_ID", root_ou_id)
        MONKEYPATCH.setenv(
            "IDENTITY_STORE_ID", identity_store_instance["IdentityStoreId"]
        )
        MONKEYPATCH.setenv("IDENTITY_STORE_ARN", identity_store_instance["InstanceArn"])

        yield {
            "root_ou_id": root_ou_id,
            "identity_store_arn": identity_store_instance["InstanceArn"],
            "identity_store_id": identity_store_instance["IdentityStoreId"],
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
            identity_store_client.delete_user(
                IdentityStoreId=identity_store_instance["IdentityStoreId"],
                UserId=user_id,
            )

        # Delete SSO groups
        for group_id in created_sso_groups.values():
            identity_store_client.delete_group(
                IdentityStoreId=identity_store_instance["IdentityStoreId"],
                GroupId=group_id,
            )

        # Delete permission sets
        for permission_set_arn in created_permission_sets.values():
            sso_admin_client.delete_permission_set(
                InstanceArn=identity_store_instance["InstanceArn"],
                PermissionSetArn=permission_set_arn,
            )
