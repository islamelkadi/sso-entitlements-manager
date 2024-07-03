################################################
#                    Imports                   #
################################################

import os
import json
import itertools
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
    organizations_client: boto3.client,
    aws_organization_definitions: list[dict],
    root_ou_id: str,
    parent_ou_id: str = "",
) -> None:
    """
    Fixture to setup AWS mock organizations by creating:
        1. Creating an AWS organization
        2. Creating AWS organizations units (OUs)
        3. Creating AWS accounts
        4. Moving those AWS accounts under their designated OU
    """
    for organization_resource in aws_organization_definitions:
        if organization_resource["type"] == "ORGANIZATIONAL_UNIT":
            # Create OU
            nested_ou_id = organizations_client.create_organizational_unit(
                ParentId=parent_ou_id if parent_ou_id else root_ou_id,
                Name=organization_resource["name"],
            )["OrganizationalUnit"]["Id"]

            # Recursively setup OU
            if organization_resource["children"]:
                create_aws_ous_accounts(
                    organizations_client,
                    organization_resource["children"],
                    root_ou_id,
                    nested_ou_id,
                )

        elif organization_resource["type"] == "ACCOUNT":
            # Create account
            account_id = organizations_client.create_account(
                Email=f"{organization_resource['name']}@testing.com",
                AccountName=organization_resource["name"],
            )["CreateAccountStatus"]["AccountId"]

            # Move account to OU
            organizations_client.move_account(
                AccountId=account_id,
                SourceParentId=root_ou_id,
                DestinationParentId=parent_ou_id,
            )


def delete_aws_ous_accounts(
    organizations_client: boto3.client, root_ou_id: str, parent_ou_id: str = ""
) -> None:
    """
    Recursively delete AWS accounts from nested organizational units (OUs).
    """

    # Function to delete accounts in the current OU
    def delete_accounts_in_ou(ou_id: str) -> None:
        accounts_to_delete = organizations_client.list_accounts_for_parent(
            ParentId=ou_id
        )["Accounts"]
        for account in accounts_to_delete:
            organizations_client.remove_account_from_organization(
                AccountId=account["Id"]
            )

    # Function to recursively delete accounts in child OUs
    def delete_accounts_in_child_ous(parent_id: str) -> None:
        child_ous_paginator = organizations_client.get_paginator("list_children")
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


################################################
#         Fixtures - AWS Env & Env Vars        #
################################################


@pytest.fixture(scope="session", autouse=True)
def set_aws_creds():
    MONKEYPATCH.setenv("AWS_REGION", "us-east-1")
    MONKEYPATCH.setenv("AWS_SESSION_TOKEN", "test")
    MONKEYPATCH.setenv("AWS_ACCESS_KEY_ID", "test")
    MONKEYPATCH.setenv("AWS_SECRET_ACCESS_KEY", "test")
    yield


@pytest.fixture(scope="session", autouse=True)
def setup_env_vars():
    MONKEYPATCH.setenv("LOG_LEVEL", "INFO")
    MONKEYPATCH.setenv("DDB_TABLE_NAME", "cloud_pass")
    MONKEYPATCH.setenv("IDENTITY_STORE_ID", "d-1234567890")
    MONKEYPATCH.setenv("IDENTITY_STORE_ARN", "arn:aws:sso:::instance/ssoins-instanceId")
    yield


################################################
#          Fixtures - Setup AWS clients        #
################################################


@pytest.fixture(scope="session")
def organizations_client() -> boto3.client:
    """
    Fixture to mock AWS Organizations client
    """
    with moto.mock_organizations():
        yield boto3.client("organizations")


@pytest.fixture(scope="session")
def identity_store_client() -> boto3.client:
    """
    Fixture to mock AWS Organizations client
    """
    with moto.mock_identitystore():
        yield boto3.client("identitystore")


@pytest.fixture(scope="session")
def sso_admin_client() -> boto3.client:
    """
    Fixture to mock AWS Organizations client
    """
    with moto.mock_ssoadmin():
        yield boto3.client("sso-admin")


################################################
#         Fixtures - AWS organizations         #
################################################


@pytest.fixture(scope="session")
def setup_aws_environment(
    request: str,
    organizations_client: boto3.client,
    identity_store_client: boto3.client,
    sso_admin_client: boto3.client,
) -> dict:
    # Load parameter from pytest marker or fixture definition
    param_value = request.param

    # Load env vars
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

    # Load JSON definitions
    cwd = os.path.dirname(os.path.realpath(__file__))
    organizations_map_path = os.path.join(cwd, "configs", "organizations", param_value)
    with open(organizations_map_path) as fp:
        aws_environment_details = json.load(fp)

    aws_organizations_definitions = aws_environment_details.get("aws_organizations", [])
    permission_set_definitions = aws_environment_details.get("permission_sets", [])
    sso_users = aws_environment_details.get("sso_users", [])
    sso_groups = aws_environment_details.get("sso_groups", [])

    root_ou_id = None
    try:

        # Setup AWS organizations
        organizations_client.create_organization()
        root_ou_id = organizations_client.list_roots()["Roots"][0]["Id"]
        
        create_aws_ous_accounts(
            organizations_client=organizations_client,
            aws_organization_definitions=aws_organizations_definitions,
            root_ou_id=root_ou_id,
        )

        # Setup AWS Identity center
        for user in sso_users:
            identity_store_client.create_user(
                IdentityStoreId=identity_store_id,
                UserName=user["username"],
                DisplayName=user["name"]["Formatted"],
                Name=user["name"],
                Emails=user["email"],
            )

        for group in sso_groups:
            identity_store_client.create_group(
                IdentityStoreId=identity_store_id,
                DisplayName=group["name"],
                Description=group["description"],
            )

        for permission_set in permission_set_definitions:
            sso_admin_client.create_permission_set(
                InstanceArn=identity_store_arn,
                Name=permission_set["name"],
                Description=permission_set["description"],
            )

        # Set Root OU ID env var
        MONKEYPATCH.setenv("ROOT_OU_ID", root_ou_id)

        yield {
            "root_ou_id": root_ou_id,
            "aws_organization_definitions": aws_organizations_definitions,
            "aws_sso_group_definitions": sso_groups,
            "aws_sso_user_definitions": sso_users,
            "aws_permission_set_definitions": permission_set_definitions,
        }
    finally:
        # Teardown logic
        if root_ou_id:
            # Remove AWS accounts from organization
            delete_aws_ous_accounts(
                organizations_client=organizations_client, root_ou_id=root_ou_id
            )

            # Delete AWS resources or undo changes as needed
            organizations_client.delete_organization(OrganizationId=root_ou_id)

            # Delete SSO users
            sso_users_paginator = identity_store_client.get_paginator("list_users")
            sso_users_iterator = sso_users_paginator.paginate(
                IdentityStoreId=identity_store_id
            )
            sso_users = list(
                itertools.chain.from_iterable(
                    (page["Users"] for page in sso_users_iterator)
                )
            )
            for user in sso_users:
                identity_store_client.delete_user(
                    IdentityStoreId=identity_store_arn, UserId=user["UserId"]
                )

            # Delete SSO groups
            sso_groups_paginator = identity_store_client.get_paginator("list_groups")
            sso_groups_iterator = sso_groups_paginator.paginate(
                IdentityStoreId=identity_store_id
            )
            sso_groups = list(
                itertools.chain.from_iterable(
                    (page["Groups"] for page in sso_groups_iterator)
                )
            )
            for group in sso_groups:
                identity_store_client.delete_group(
                    IdentityStoreId=identity_store_arn, GroupId=group["GroupId"]
                )

            # Delete permission sets
            permission_sets_paginator = sso_admin_client.get_paginator(
                "list_permission_sets"
            )
            permission_sets_iterator = permission_sets_paginator.paginate(
                InstanceArn=identity_store_arn
            )
            permission_sets = list(
                itertools.chain.from_iterable(
                    (page["PermissionSets"] for page in permission_sets_iterator)
                )
            )
            for permission_set in permission_sets:
                sso_admin_client.delete_permission_set(
                    InstanceArn=identity_store_arn, PermissionSetArn=permission_set
                )
