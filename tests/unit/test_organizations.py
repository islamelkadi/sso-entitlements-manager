# pylint: disable=E1120
"""
Unit tests for AwsOrganizations to testr listing AWS accounts, handling organizational units,
and excluding specific accounts and organizational units.

Tests:
- test_missing_constructor_parameter:
    Proper initialization with required parameters.
- test_list_active_aws_accounts_include_all_organiational_units:
    Correct listing of active AWS accounts.
- test_list_active_aws_accounts_exclude_suspended_organizational_unit:
    Exclusion of suspended and specific AWS accounts.
- test_list_active_aws_accounts_exclude_multiple_organizational_units:
    Exclusion of multiple AWS accounts.
- test_list_active_aws_accounts_exclude_specific_account:
    Exclusion of specific AWS account.
- test_list_active_aws_accounts_exclude_multiple_specific_accounts:
    Exclusion of multiple specific AWS accounts.
- test_list_active_aws_accounts_exclude_specific_accounts_and_organizational_units:
    Exclusion of specific accounts and organizational units.
- Use of setup fixtures for environment configuration.
"""

import itertools
import boto3
import pytest
from app.lib.ou_accounts_mapper import AwsOrganizations


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


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_include_all_organiational_units(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    """
    Test case to verify listing active AWS accounts including all organizational units.

    Parameters:
    ----------
    organizations_client: boto3.client
        Fixture providing an AWS Organizations client.
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via
    AwsOrganizations does not match boto3's list_accounts.
    """
    # Arrange
    root_ou_id = setup_aws_environment["root_ou_id"]
    py_aws_organizations = AwsOrganizations(root_ou_id)

    # Act
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(
        itertools.chain(*py_aws_organizations.ou_account_map.values())
    )

    # Assert
    assert len(active_aws_accounts_via_boto3) == len(active_aws_accounts_via_class)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_suspended_organizational_unit(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    """
    Test case to verify listing active AWS accounts excluding suspended organizational unit.

    Parameters:
    ----------
    organizations_client: boto3.client
        Fixture providing an AWS Organizations client.
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id and aws_organization_definitions.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via AwsOrganizations, excluding
    suspended OU, does not match boto3's list_accounts.
    """
    # Arrange
    ignored_ou_list = ["suspended"]
    root_ou_id = setup_aws_environment["root_ou_id"]
    organization_map = setup_aws_environment["aws_organization_definitions"]
    suspended_ou_accounts = list(
        itertools.chain(
            *[
                item["children"]
                for item in organization_map
                if item["name"] in ignored_ou_list
            ]
        )
    )

    # Act
    py_aws_organizations = AwsOrganizations(root_ou_id, ignored_ou_list)
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(
        itertools.chain(*py_aws_organizations.ou_account_map.values())
    )

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(suspended_ou_accounts) == len(
        active_aws_accounts_via_class
    )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_multiple_organizational_units(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    """
    Test case to verify listing active AWS accounts excluding multiple organizational units.

    Parameters:
    ----------
    organizations_client: boto3.client
        Fixture providing an AWS Organizations client.
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id and aws_organization_definitions.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via AwsOrganizations, excluding
    specified OUs, does not match boto3's list_accounts.
    """
    # Arrange
    ignored_ou_list = ["suspended", "prod"]
    root_ou_id = setup_aws_environment["root_ou_id"]
    organization_map = setup_aws_environment["aws_organization_definitions"]
    ignored_ou_accounts = list(
        itertools.chain(
            *[
                item["children"]
                for item in organization_map
                if item["name"] in ignored_ou_list
            ]
        )
    )

    # Act
    py_aws_organizations = AwsOrganizations(root_ou_id, ignored_ou_list)
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(
        itertools.chain(*py_aws_organizations.ou_account_map.values())
    )

    # Assert
    assert len(active_aws_accounts_via_class) == len(
        active_aws_accounts_via_boto3
    ) - len(ignored_ou_accounts)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_specific_account(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    """
    Test case to verify listing active AWS accounts excluding a specific account.

    Parameters:
    ----------
    organizations_client: boto3.client
        Fixture providing an AWS Organizations client.
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via AwsOrganizations, excluding
    specified accounts, does not match boto3's list_accounts.
    """
    # Arrange
    ignored_account_list = ["workload_1_dev"]
    root_ou_id = setup_aws_environment["root_ou_id"]

    # Act
    py_aws_organizations = AwsOrganizations(
        root_ou_id, exclude_account_name_list=ignored_account_list
    )
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(
        itertools.chain(*py_aws_organizations.ou_account_map.values())
    )

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(ignored_account_list) == len(
        active_aws_accounts_via_class
    )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_multiple_specific_accounts(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    """
    Test case to verify listing active AWS accounts excluding multiple specific accounts.

    Parameters:
    ----------
    organizations_client: boto3.client
        Fixture providing an AWS Organizations client.
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via AwsOrganizations, excluding
    specified accounts, does not match boto3's list_accounts.
    """
    # Arrange
    ignored_account_list = ["workload_1_dev", "workload_2_test", "workload_2_prod"]
    root_ou_id = setup_aws_environment["root_ou_id"]

    # Act
    py_aws_organizations = AwsOrganizations(
        root_ou_id, exclude_account_name_list=ignored_account_list
    )
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(
        itertools.chain(*py_aws_organizations.ou_account_map.values())
    )

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(ignored_account_list) == len(
        active_aws_accounts_via_class
    )


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_specific_accounts_and_organizational_units(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    """
    Test case to verify listing active AWS accounts excluding specific accounts
    and organizational units.

    Parameters:
    ----------
    organizations_client: boto3.client
        Fixture providing an AWS Organizations client.
    setup_aws_environment: pytest.fixture
        Fixture providing setup data including root_ou_id and aws_organization_definitions.

    Raises:
    ------
    AssertionError: If the number of active accounts retrieved via AwsOrganizations, excluding
    specified accounts and OUs, does not match boto3's list_accounts.
    """
    # Arrange
    ignored_ou_list = ["suspended", "prod"]
    ignored_specific_account_list = ["workload_1_dev", "workload_2_test"]

    root_ou_id = setup_aws_environment["root_ou_id"]
    organization_map = setup_aws_environment["aws_organization_definitions"]

    ignored_ou_accounts = []
    for ou in organization_map:
        if ou["name"] in ignored_ou_list:
            for item in ou["children"]:
                if item["type"] == "ACCOUNT":
                    ignored_ou_accounts.append(item["name"])

    # Act
    py_aws_organizations = AwsOrganizations(
        root_ou_id, ignored_ou_list, ignored_specific_account_list
    )
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(
        itertools.chain(*py_aws_organizations.ou_account_map.values())
    )

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(
        set(ignored_specific_account_list + ignored_ou_accounts)
    ) == len(active_aws_accounts_via_class)
