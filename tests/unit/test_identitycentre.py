# pylint: disable=E1120
"""
Unit tests to validate functionality of AwsIdentityCentre from identity_center_mapper.

Tests:
- test_missing_default_constructor_parameters:
    Verify TypeError is raised when identity_store_arn parameter is missing.
- test_list_identity_center_entities:
    Test listing SSO groups, users, and permission sets using pytest parameterization
    and indirect fixture setup_aws_environment.
"""

import os
import pytest
from app.lib.identity_center_mapper import AwsIdentityCentre


def test_missing_default_constructor_parameters() -> None:
    """
    Test case for missing identity_store_arn or identity_store_id parameter
    in AwsIdentityCentre constructor.

    Raises:
    ------
    TypeError: If identity_store_arn or identity_store_id parameter is missing
    during AwsIdentityCentre instantiation.
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre()

    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_id=identity_store_id)

    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_arn=identity_store_arn)

@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_list_identity_center_entities(setup_aws_environment: pytest.fixture) -> None:
    """
    Test case for listing SSO groups, users, and permission sets and make sure they
    were successfully created.

    Parameters:
    ----------
    setup_aws_environment: pytest.fixture
        Fixture that sets up AWS environment with aws_org_1.json data.

    Raises:
    ------
    AssertionError: If the number of SSO groups, users, or permission sets retrieved does not
    match the expected number from setup_aws_environment.
    """
    # Arrange
    identity_store_id = os.getenv("IDENTITY_STORE_ID")
    identity_store_arn = os.getenv("IDENTITY_STORE_ARN")

    # Act
    py_aws_sso = AwsIdentityCentre(identity_store_id, identity_store_arn)

    # Assert
    assert len(py_aws_sso.sso_users) == len(setup_aws_environment["aws_sso_user_definitions"])
    assert len(py_aws_sso.sso_groups) == len(setup_aws_environment["aws_sso_group_definitions"])
    assert len(py_aws_sso.permission_sets) == len(setup_aws_environment["aws_permission_set_definitions"])
