# pylint: disable=E1120
"""
Unit tests for AwsOrganizations to test listing AWS accounts, handling
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
from app.lib.ous_accounts_mapper import AwsOrganizations


def test_missing_constructor_parameter() -> None:
    """
    Test case to verify that AwsOrganizations raises TypeError when
    instantiated without required parameters.

    Raises:
    ------
    pytest.raises(TypeError): If AwsOrganizations is instantiated without required parameters.
    """
    # Arrange
    with pytest.raises(TypeError):
        # Act
        AwsOrganizations()


@pytest.mark.parametrize(
    "setup_aws_environment, excluded_ous, excluded_accounts",
    [
        ("aws_org_1.json", [], []),
        ("aws_org_1.json", ["suspended"], []),
        ("aws_org_1.json", ["suspended", "prod"], []),
        ("aws_org_1.json", [], ["workload_1_dev"]),
        ("aws_org_1.json", [], ["workload_1_dev", "workload_2_test", "workload_2_prod"]),
        ("aws_org_1.json", ["suspended", "prod"], ["workload_1_dev", "workload_2_test"]),
    ],
    indirect=["setup_aws_environment"],
)
def test_list_active_included_aws_accounts(
    organizations_client: boto3.client,
    setup_aws_environment: pytest.fixture,
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
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id and aws_organization_definitions.
    excluded_ous: list
        List of specific OU names to exclude from account listing.
    excluded_accounts: list
        List of specific account names to exclude from account listing.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via AwsOrganizations, excluding
    specified accounts and OUs, does not match boto3's list_accounts.
    """
    # Arrange
    root_ou_id = setup_aws_environment["root_ou_id"]
    organization_map = setup_aws_environment["aws_organization_definitions"]

    # Gather account names to exclude from specified OUs
    excluded_ou_accounts = [item["name"] for ou in organization_map if ou["name"] in excluded_ous for item in ou["children"] if item["type"] == "ACCOUNT"]
    accounts_to_filter_out = set(excluded_ou_accounts + excluded_accounts)

    # Act
    py_aws_organizations = AwsOrganizations(root_ou_id)
    setattr(py_aws_organizations, "exclude_ou_name_list", excluded_ous)
    setattr(py_aws_organizations, "exclude_account_name_list", excluded_accounts)
    py_aws_organizations.run_ous_accounts_mapper()

    active_aws_accounts_via_class = [x["Name"] for x in list(itertools.chain(*py_aws_organizations.ou_accounts_map.values()))]
    active_aws_account_names_via_boto3 = [x["Name"] for x in organizations_client.list_accounts()["Accounts"] if x["Name"] not in accounts_to_filter_out]

    # Assert
    assert sorted(active_aws_accounts_via_class) == sorted(active_aws_account_names_via_boto3)
