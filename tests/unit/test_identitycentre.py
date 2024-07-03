"""
Unit tests to test writing regex rules from DDB
"""
import os
import pytest
from app.lib.aws_identitycentre import AwsIdentityCentre


def test_missing_constructor_identitystore_arn_parameter() -> None:
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")

    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_id=identity_store_id)


def test_missing_constructor_identitystore_id_parameter() -> None:
    # Arrange
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_arn=identity_store_arn)


def test_missing_constructor_identitystore_arn_id_parameters() -> None:
    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre()


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_sso_groups(setup_aws_environment: pytest.fixture) -> None:
    """
    Test list SSO groups
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")
    sso_groups_definitions = setup_aws_environment["aws_sso_group_definitions"]

    # Act
    py_aws_sso = AwsIdentityCentre(identity_store_id, identity_store_arn)

    # Assert
    assert len(py_aws_sso.sso_groups) == len(sso_groups_definitions)


@pytest.mark.parametrize(
    "setup_aws_environment", ["aws_org_1.json"], indirect=True
)
def test_list_users(setup_aws_environment: pytest.fixture) -> None:
    """
    Test list SSO groups
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")
    users_definitions = setup_aws_environment["aws_sso_user_definitions"]

    # Act
    py_aws_sso = AwsIdentityCentre(identity_store_id, identity_store_arn)

    # Assert
    assert len(py_aws_sso.sso_users) == len(users_definitions)


@pytest.mark.parametrize(
    "setup_aws_environment", ["aws_org_1.json"], indirect=True
)
def test_list_permission_sets(setup_aws_environment: pytest.fixture) -> None:
    """
    Test list SSO groups
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

    # Act
    py_aws_organizations = AwsIdentityCentre(identity_store_id, identity_store_arn)

    # Assert
    assert len(py_aws_organizations.permission_sets) == len(setup_aws_environment["aws_permission_set_definitions"])
