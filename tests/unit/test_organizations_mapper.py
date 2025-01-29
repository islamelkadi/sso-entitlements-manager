# pylint: disable=E1120
"""
Unit tests for OrganizationsMapper to test listing AWS accounts, handling
organizational units, and excluding specific accounts and organizational units.

Tests:
- test_missing_constructor_parameter:
    Proper initialization with required parameters.
- test_list_active_included_aws_accounts:
    Correct listing of active AWS accounts.
"""

import boto3
import pytest
from src.services.aws.organizations_mapper import OrganizationsMapper


@pytest.mark.parametrize(
    "setup_mock_aws_environment",
    ["aws_org_1.json", "aws_org_2.json"],
    indirect=["setup_mock_aws_environment"],
)
def test_list_active_included_aws_accounts(organizations_client: boto3.client, setup_mock_aws_environment: pytest.fixture) -> None:
    """
    Test case to verify listing active AWS accounts with optional
    exclusion of specific OUs and accounts.

    Parameters:
    ----------
    organizations_client: boto3.client
        Fixture providing an AWS Organizations client.
    setup_mock_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id and aws_organization_definitions.
    excluded_ous: list
        List of specific OU names to exclude from account listing.
    excluded_accounts: list
        List of specific account names to exclude from account listing.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via OrganizationsMapper, excluding
    specified accounts and OUs, does not match boto3's list_accounts.
    """
    # Arrange
    py_aws_organizations = OrganizationsMapper()

    # Act
    active_aws_accounts_via_class: list[str] = []
    for ou in py_aws_organizations.ou_accounts_map.values():
        for account in ou["Accounts"]:
            active_aws_accounts_via_class.append(account["Name"])

    active_aws_account_names_via_boto3: list[str] = []
    for account in organizations_client.list_accounts()["Accounts"]:
        if account["Status"] == "ACTIVE":
            active_aws_account_names_via_boto3.append(account["Name"])

    # Assert
    assert sorted(active_aws_accounts_via_class) == sorted(active_aws_account_names_via_boto3)
