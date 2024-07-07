"""
Unit tests to test writing regex rules from DDB
"""
import itertools
import boto3
import pytest
from app.lib.ou_accounts_mapper import AwsOrganizations


def test_missing_constructor_parameter() -> None:
    # Arrange
    with pytest.raises(TypeError):
        AwsOrganizations()


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_include_all_organiational_units(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    # Arrange
    root_ou_id = setup_aws_environment["root_ou_id"]
    py_aws_organizations = AwsOrganizations(root_ou_id)

    # Act
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(itertools.chain(*py_aws_organizations.ou_account_map.values()))

    # Assert
    assert len(active_aws_accounts_via_boto3) == len(active_aws_accounts_via_class)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_suspended_organizational_unit(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    # Arrange
    ignored_ou_list = ["suspended"]
    root_ou_id = setup_aws_environment["root_ou_id"]
    organization_map = setup_aws_environment["aws_organization_definitions"]
    suspended_ou_accounts = list(itertools.chain(*[item["children"] for item in organization_map if item["name"] in ignored_ou_list]))

    # Act
    py_aws_organizations = AwsOrganizations(root_ou_id, ignored_ou_list)
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(itertools.chain(*py_aws_organizations.ou_account_map.values()))

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(suspended_ou_accounts) == len(active_aws_accounts_via_class)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_multiple_organizational_units(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    # Arrange
    ignored_ou_list = ["suspended", "prod"]
    root_ou_id = setup_aws_environment["root_ou_id"]
    organization_map = setup_aws_environment["aws_organization_definitions"]
    ignored_ou_accounts = list(itertools.chain(*[item["children"] for item in organization_map if item["name"] in ignored_ou_list]))

    # Act
    py_aws_organizations = AwsOrganizations(root_ou_id, ignored_ou_list)
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(itertools.chain(*py_aws_organizations.ou_account_map.values()))

    # Assert
    assert len(active_aws_accounts_via_class) == len(active_aws_accounts_via_boto3) - len(ignored_ou_accounts)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_specific_account(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    # Arrange
    ignored_account_list = ["workload_1_dev"]
    root_ou_id = setup_aws_environment["root_ou_id"]

    # Act
    py_aws_organizations = AwsOrganizations(root_ou_id, exclude_account_name_list = ignored_account_list)
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(itertools.chain(*py_aws_organizations.ou_account_map.values()))

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(ignored_account_list) == len(active_aws_accounts_via_class)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_multiple_specific_accounts(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
    # Arrange
    ignored_account_list = ["workload_1_dev", "workload_2_test", "workload_2_prod"]
    root_ou_id = setup_aws_environment["root_ou_id"]

    # Act
    py_aws_organizations = AwsOrganizations(root_ou_id, exclude_account_name_list = ignored_account_list)
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(itertools.chain(*py_aws_organizations.ou_account_map.values()))

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(ignored_account_list) == len(active_aws_accounts_via_class)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_active_aws_accounts_exclude_multiple_specific_accounts(
    organizations_client: boto3.client, setup_aws_environment: pytest.fixture
) -> None:
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
    py_aws_organizations = AwsOrganizations(root_ou_id, ignored_ou_list, ignored_specific_account_list)
    active_aws_accounts_via_boto3 = organizations_client.list_accounts()["Accounts"]
    active_aws_accounts_via_class = list(itertools.chain(*py_aws_organizations.ou_account_map.values()))

    # Assert
    assert len(active_aws_accounts_via_boto3) - len(set(ignored_specific_account_list + ignored_ou_accounts)) == len(active_aws_accounts_via_class)
