# pylint: disable=E1120
"""
Unit Tests for AWS Organizations Manager

This module contains comprehensive test cases for validating the AwsOrganizationsManager's 
functionality, focusing on:
    - AWS account listing
    - Organizational unit handling
    - Account and OU exclusion mechanisms
"""

import boto3
import pytest
from src.services.aws.aws_organizations_manager import AwsOrganizationsManager


@pytest.mark.parametrize(
    "setup_mock_aws_environment",
    ["aws_org_1.json", "aws_org_2.json"],
    indirect=["setup_mock_aws_environment"],
)
def test_list_active_included_aws_accounts(
    organizations_client: boto3.client, setup_mock_aws_environment: pytest.fixture
) -> None:
    """
    This test compares accounts retrieved via AwsOrganizationsManager against
    those retrieved directly through boto3's list_accounts method.

    Test Strategy:
        1. Initializes AwsOrganizationsManager with root OU ID
        2. Extracts account names from OU accounts map
        3. Retrieves active account names using boto3 list_accounts
        4. Compares sorted lists of account names

    Args:
        organizations_client (boto3.client): Mocked AWS Organizations client
        setup_mock_aws_environment (pytest.fixture): Fixture providing mockAWS environment setup

    Asserts:
        The active account names retrieved via the Boto3 API is the same as
        that retrieved via the AwsOrganizationsManager class

    Note:
        This test assumes:
            - All accounts in the organization are active
            - Account names are unique and consistent across retrieval methods
    """
    # Arrange
    root_ou_id = setup_mock_aws_environment["root_ou_id"]
    py_aws_organizations = AwsOrganizationsManager(root_ou_id)

    # Act
    active_aws_accounts_via_class: list[str] = []
    for accounts_information in py_aws_organizations.ou_accounts_map.values():
        for account in accounts_information:
            active_aws_accounts_via_class.append(account["Name"])

    active_aws_account_names_via_boto3: list[str] = []
    for account in organizations_client.list_accounts()["Accounts"]:
        if account["Status"] == "ACTIVE":
            active_aws_account_names_via_boto3.append(account["Name"])

    # Assert
    assert sorted(active_aws_accounts_via_class) == sorted(
        active_aws_account_names_via_boto3
    )
