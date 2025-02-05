# pylint: disable=E1120
"""
Unit tests to validate functionality of AwsIdentityCentre from identity_center_mapper.

Tests:
- test_missing_default_constructor_parameters:
    Verify TypeError is raised when identity_store_arn parameter is missing.
- test_list_identity_center_entities:
    Test listing SSO groups, users, and permission sets using pytest parameterization
    and indirect fixture setup_mock_aws_environment.
"""

import pytest
from src.services.aws.sso_admin_mapper import SsoAdminMapper


@pytest.mark.parametrize(
    "setup_mock_aws_environment",
    ["aws_org_1.json", "aws_org_2.json"],
    indirect=["setup_mock_aws_environment"],
)
def test_list_sso_admin_entities(setup_mock_aws_environment: pytest.fixture) -> None:
    # Arrange/Act
    identity_store_arn = setup_mock_aws_environment["identity_store_arn"]
    identity_store_id = setup_mock_aws_environment["identity_store_id"]
    sso_admin_mapper = SsoAdminMapper(identity_store_arn, identity_store_id)

    # Assert
    sso_usernames_via_class = sso_admin_mapper.sso_environment["users"]
    assert sso_usernames_via_class == setup_mock_aws_environment["sso_username_id_map"]

    sso_groups_via_class = sso_admin_mapper.sso_environment["groups"]
    assert sso_groups_via_class == setup_mock_aws_environment["sso_group_name_id_map"]

    permission_sets_via_class = sso_admin_mapper.sso_environment["permission_sets"]
    assert permission_sets_via_class == setup_mock_aws_environment["sso_permission_set_name_id_map"]
