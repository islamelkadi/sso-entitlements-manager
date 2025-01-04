# pylint: disable=E1120
"""
Unit tests for AwsOrganizationsMapper to test listing AWS accounts, handling
organizational units, and excluding specific accounts and organizational units.

Tests:
- test_missing_constructor_parameter:
    Proper initialization with required parameters.
- test_list_active_included_aws_accounts:
    Correct listing of active AWS accounts.
"""

import itertools
from typing import List
import boto3
import pytest
from src.services.aws_organizations_mapper import AwsOrganizationsMapper


@pytest.mark.parametrize(
    "setup_mock_aws_environment, excluded_ous, excluded_accounts",
    [
        ("aws_org_1.json", [], []),
        ("aws_org_1.json", ["suspended"], []),
        ("aws_org_1.json", ["suspended", "prod"], []),
        ("aws_org_1.json", [], ["workload_1_dev"]),
        (
            "aws_org_1.json",
            [],
            ["workload_1_dev", "workload_2_test", "workload_2_prod"],
        ),
        (
            "aws_org_1.json",
            ["suspended", "prod"],
            ["workload_1_dev", "workload_2_test"],
        ),
    ],
    indirect=["setup_mock_aws_environment"],
)
def test_list_active_included_aws_accounts(
    organizations_client: boto3.client,
    setup_mock_aws_environment: pytest.fixture,
    excluded_ous: List[str],
    excluded_accounts: List[str],
) -> None:
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
    AssertionError: If the number of active accounts retrieved via AwsOrganizationsMapper, excluding
    specified accounts and OUs, does not match boto3's list_accounts.
    """
    # Arrange
    excluded_ou_accounts = []
    for ou, accounts in setup_mock_aws_environment["ou_accounts_map"].items():
        if ou in excluded_ous:
            excluded_ou_accounts.extend([x["Name"] for x in accounts])
    accounts_to_filter_out = set(excluded_ou_accounts + excluded_accounts)

    # Act
    py_aws_organizations = AwsOrganizationsMapper()
    setattr(py_aws_organizations, "exclude_ou_name_list", excluded_ous)
    setattr(py_aws_organizations, "exclude_account_name_list", excluded_accounts)
    py_aws_organizations.run_ous_accounts_mapper()

    active_aws_accounts_via_class = [x["Name"] for x in list(itertools.chain(*py_aws_organizations.ou_accounts_map.values()))]
    active_aws_account_names_via_boto3 = [x["Name"] for x in organizations_client.list_accounts()["Accounts"] if x["Name"] not in accounts_to_filter_out]

    # Assert
    assert sorted(active_aws_accounts_via_class) == sorted(active_aws_account_names_via_boto3)
