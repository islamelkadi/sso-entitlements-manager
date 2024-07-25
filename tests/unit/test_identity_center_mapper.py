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
from typing import List
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


@pytest.mark.parametrize(
    "setup_aws_environment, excluded_sso_users, excluded_sso_groups, excluded_permission_sets",
    [
        ("aws_org_1.json", ["user1@testing.com"], [], []),
        ("aws_org_1.json", [], ["group1"], []),
        ("aws_org_1.json", [], [], ["Administrator"]),
        ("aws_org_1.json", ["user1@testing.com", "user2@testing.com"], [], []),
        ("aws_org_1.json", [], ["group1", "group2"], []),
        ("aws_org_1.json", [], [], ["Administrator", "ReadOnly"]),
        ("aws_org_1.json", ["user1@testing.com"], ["group1"], []),
        ("aws_org_1.json", ["user1@testing.com", "user2@testing.com"], ["group1"], []),
        ("aws_org_1.json", ["user1@testing.com"], ["group1", "group2"], []),
        ("aws_org_1.json", ["user1@testing.com"], [], ["Administrator", "ReadOnly"]),
    ],
    indirect=["setup_aws_environment"],
)
def test_list_identity_center_entities(setup_aws_environment: pytest.fixture, excluded_sso_users: List[str], excluded_sso_groups: List[str], excluded_permission_sets: List[str]) -> None:
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
    setattr(py_aws_sso, "exclude_sso_users", excluded_sso_users)
    setattr(py_aws_sso, "exclude_sso_groups", excluded_sso_groups)
    setattr(py_aws_sso, "exclude_permission_sets", excluded_permission_sets)
    py_aws_sso.run_identity_center_mapper()

    # Assert
    sso_usernames_via_class = list(py_aws_sso.sso_users.keys())
    sso_usernames_via_definitions = [x["username"] for x in setup_aws_environment["aws_sso_user_definitions"] if x["username"] not in excluded_sso_users]
    assert sorted(sso_usernames_via_class) == sorted(sso_usernames_via_definitions)

    sso_groups_via_class = list(py_aws_sso.sso_groups.keys())
    sso_groups_via_definitions = [x["name"] for x in setup_aws_environment["aws_sso_group_definitions"] if x["name"] not in excluded_sso_groups]
    assert sorted(sso_groups_via_class) == sorted(sso_groups_via_definitions)

    permission_sets_via_class = list(py_aws_sso.permission_sets.keys())
    permission_sets_via_definitions = [x["name"] for x in setup_aws_environment["aws_permission_set_definitions"] if x["name"] not in excluded_permission_sets]
    assert sorted(permission_sets_via_class) == sorted(permission_sets_via_definitions)
