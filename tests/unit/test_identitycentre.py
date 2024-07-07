"""
Unit tests to validate functionality of AwsIdentityCentre from identity_center_mapper.

Tests:
- test_missing_constructor_identitystore_arn_parameter:
    Verify TypeError is raised when identity_store_arn parameter is missing.
- test_missing_constructor_identitystore_id_parameter:
    Verify TypeError is raised when identity_store_id parameter is missing.
- test_missing_constructor_identitystore_arn_id_parameters:
    Verify TypeError is raised when both identity_store_id and identity_store_arn
    parameters are missing.
- test_list_sso_groups:
    Test listing SSO groups using pytest parameterization and indirect
    fixture setup_aws_environment.
- test_list_users:
    Test listing SSO users using pytest parameterization and indirect
    fixture setup_aws_environment.
- test_list_permission_sets:
    Test listing permission sets using pytest parameterization and indirect
    fixture setup_aws_environment.
"""

import os
import pytest
from app.lib.identity_center_mapper import AwsIdentityCentre


def test_missing_constructor_identitystore_arn_parameter() -> None:
    """
    Test case for missing identity_store_arn parameter in AwsIdentityCentre constructor.

    Raises:
    ------
    TypeError: If identity_store_arn parameter is missing during AwsIdentityCentre instantiation.
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")

    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_id=identity_store_id)


def test_missing_constructor_identitystore_id_parameter() -> None:
    """
    Test case for missing identity_store_id parameter in AwsIdentityCentre constructor.

    Raises:
    ------
    TypeError: If identity_store_id parameter is missing during AwsIdentityCentre instantiation.
    """
    # Arrange
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_arn=identity_store_arn)


def test_missing_constructor_identitystore_arn_id_parameters() -> None:
    """
    Test case for missing both identity_store_id and identity_store_arn
    parameters in AwsIdentityCentre constructor.

    Raises:
    ------
    TypeError: If both identity_store_id and identity_store_arn
    parameters are missing during AwsIdentityCentre instantiation.
    """
    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre()


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_sso_groups(setup_aws_environment: pytest.fixture) -> None:
    """
    Test case for listing SSO groups.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    AssertionError: If the number of SSO groups retrieved does not
    match the expected number from setup_aws_environment.
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")
    sso_groups_definitions = setup_aws_environment["aws_sso_group_definitions"]

    # Act
    py_aws_sso = AwsIdentityCentre(identity_store_id, identity_store_arn)

    # Assert
    assert len(py_aws_sso.sso_groups) == len(sso_groups_definitions)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_users(setup_aws_environment: pytest.fixture) -> None:
    """
    Test case for listing SSO users.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    AssertionError: If the number of SSO users retrieved does not match
    the expected number from setup_aws_environment.
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")
    users_definitions = setup_aws_environment["aws_sso_user_definitions"]

    # Act
    py_aws_sso = AwsIdentityCentre(identity_store_id, identity_store_arn)

    # Assert
    assert len(py_aws_sso.sso_users) == len(users_definitions)


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_permission_sets(setup_aws_environment: pytest.fixture) -> None:
    """
    Test case for listing permission sets.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    AssertionError: If the number of permission sets retrieved does not
    match the expected number from setup_aws_environment.
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

    # Act
    py_aws_organizations = AwsIdentityCentre(identity_store_id, identity_store_arn)

    # Assert
    assert len(py_aws_organizations.permission_sets) == len(
        setup_aws_environment["aws_permission_set_definitions"]
    )
