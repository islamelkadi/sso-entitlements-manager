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

from typing import List
import pytest
from app.lib.identity_center_mapper import AwsIdentityCentre


@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"])
def test_missing_default_constructor_parameters(setup_aws_environment: pytest.fixture) -> None:
    """
    Test case for missing identity_store_arn or identity_store_id parameter
    in AwsIdentityCentre constructor.

    Raises:
    ------
    TypeError: If identity_store_arn or identity_store_id parameter is missing
    during AwsIdentityCentre instantiation.
    """

    # Assert
    with pytest.raises(TypeError):
        AwsIdentityCentre()

    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_id=setup_aws_environment["identity_center_id"])

    with pytest.raises(TypeError):
        AwsIdentityCentre(identity_store_arn=setup_aws_environment["identity_center_arn"])


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
    py_aws_sso = AwsIdentityCentre(setup_aws_environment["identity_center_id"], setup_aws_environment["identity_center_arn"])
    setattr(py_aws_sso, "exclude_sso_users", excluded_sso_users)
    setattr(py_aws_sso, "exclude_sso_groups", excluded_sso_groups)
    setattr(py_aws_sso, "exclude_permission_sets", excluded_permission_sets)

    # Act
    py_aws_sso.run_identity_center_mapper()

    # Assert
    sso_usernames_via_definitions = {username: userid for username, userid in setup_aws_environment["sso_username_id_map"].items() if username not in excluded_sso_users}
    assert py_aws_sso.sso_users == sso_usernames_via_definitions

    # sso_groups_via_definitions = [x["name"] for x in setup_aws_environment["sso_group_name_id_map"] if x["name"] not in excluded_sso_groups]
    sso_groups_via_definitions = {groupname: groupid for groupname, groupid in setup_aws_environment["sso_group_name_id_map"].items() if groupname not in excluded_sso_groups}
    assert py_aws_sso.sso_groups == sso_groups_via_definitions

    permission_sets_via_definitions = {permission_set_name: permission_set_id for permission_set_name, permission_set_id in setup_aws_environment["sso_permission_set_name_id_map"].items() if permission_set_name not in excluded_permission_sets}
    assert py_aws_sso.permission_sets == permission_sets_via_definitions
