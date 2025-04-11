# pylint: disable=E1120
"""
Unit Tests for AWS Identity Center Management

This module provides comprehensive test cases for the IdentityCenterManager,
validating various aspects of AWS Identity Center functionality, including:
    - SSO entity listing (users, groups, permission sets)
    - Account assignment creation and deletion
    - Invalid assignment reporting
"""
import os
import glob
import operator
import itertools
import concurrent.futures
from typing import Dict, List, Any

import pytest
from tests.utils import generate_expected_account_assignments
from src.core.utils import load_file
from src.core.constants import (
    PERMISSION_SET_TYPE_LABEL,
    GROUP_PRINCIPAL_TYPE_LABEL,
    USER_PRINCIPAL_TYPE_LABEL,
)
from src.services.aws.aws_identity_center_manager import (
    IdentityCenterManager,
    InvalidAssignmentRule,
)


# Globals vars
CWD = os.path.dirname(os.path.realpath(__file__))

PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES = [
    round(i * 0.2, 2) for i in range(6)
]  # 20% increments

AWS_ORG_DEFINITIONS_FILES_PATH = os.path.join(
    CWD, "..", "configs", "organizations", "*.json"
)
AWS_ORG_DEFINITION_FILES = [
    os.path.basename(x) for x in glob.glob(AWS_ORG_DEFINITIONS_FILES_PATH)
]

VALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(
    CWD, "..", "manifests", "valid_schema", "*.yaml"
)
VALID_MANIFEST_DEFINITION_FILES = [
    os.path.abspath(x) for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)
]


@pytest.mark.parametrize(
    "setup_mock_aws_environment",
    ["aws_org_1.json", "aws_org_2.json"],
    indirect=["setup_mock_aws_environment"],
)
def test_list_sso_admin_entities(setup_mock_aws_environment: pytest.fixture) -> None:
    """
    Test retrieving SSO entities from the IdentityCenterManager.

    Validates the correct retrieval of:
        - SSO users
        - SSO groups
        - SSO permission sets

    Uses a parameterized mock AWS environment to test with different
    organizational configurations.

    Args:
        setup_mock_aws_environment (pytest.fixture): Fixture providing mock
        AWS environment details, including:
            - identity_store_arn
            - identity_store_id
            - sso_username_id_map
            - sso_group_name_id_map
            - sso_permission_set_name_id_map

        - Verifies that SSO usernames retrieved by the
          IdentityCenterManager match the expected username-ID map from
          the mock AWS environment. This ensures accurate user retrieval
          and mapping.

        - Confirms that SSO groups retrieved by the
          IdentityCenterManager exactly match the expected group name-ID
          map from the mock AWS environment. This validates the correct
          extraction and mapping of SSO groups.

        - Checks that SSO permission sets retrieved by the
          IdentityCenterManager precisely correspond to the expected
          permission set name-ID map from the mock AWS environment. This
          verifies accurate permission set discovery and identification.


    Raises:
        AssertionError: If retrieved entities do not match expected values
    """
    # Arrange/Act
    identity_center_manager = IdentityCenterManager(
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["identity_store_id"],
    )

    # Assert
    sso_usernames_via_class = identity_center_manager.sso_users
    assert sso_usernames_via_class == setup_mock_aws_environment["sso_username_id_map"]

    sso_groups_via_class = identity_center_manager.sso_groups
    assert sso_groups_via_class == setup_mock_aws_environment["sso_group_name_id_map"]

    permission_sets_via_class = identity_center_manager.sso_permission_sets
    assert (
        permission_sets_via_class
        == setup_mock_aws_environment["sso_permission_set_name_id_map"]
    )


@pytest.mark.parametrize(
    "account_assignment_range, setup_mock_aws_environment, manifest_filename",
    list(
        itertools.product(
            PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES,
            AWS_ORG_DEFINITION_FILES,
            VALID_MANIFEST_DEFINITION_FILES,
        )
    ),
    indirect=["setup_mock_aws_environment"],
)
def test_create_account_assignments(
    sso_admin_client,
    account_assignment_range: float,
    setup_mock_aws_environment: pytest.fixture,
    manifest_filename: str,
) -> None:
    """
    Test the creation of account assignments based on manifest file and environment.

    Test Strategy:
        1. Generates expected account assignments
        2. Pre-creates permission set assignments using a subset of
        the expected account assignments
        3. Generates a list of account assignments to create via the
        IdentityCenterManager class based on the assignments that
        do not exist on the cloud
        4. Compares the list ofexpected account assignments to create
        to the list generate by the IdentityCenterManager class

    Args:
        sso_admin_client: Mock AWS SSO admin client for creating assignments
        account_assignment_range (float): Percentage of assignments to pre-create
        setup_mock_aws_environment (pytest.fixture): Fixture with mock AWS environment details
        manifest_filename (str): Path to the manifest file defining RBAC rules

    Asserts:
        Verifies that the assignments created match the expected assignments
        not yet pre-created in the test environment.
    """
    sort_keys = operator.itemgetter(
        "PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId"
    )
    manifest_file = load_file(manifest_filename)
    rbac_rules = manifest_file.get("rbac_rules", [])

    # Generate expected account assignments
    expected_account_assignments = generate_expected_account_assignments(
        manifest_file,
        setup_mock_aws_environment["ou_accounts_map"],
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["account_name_id_map"],
        setup_mock_aws_environment["sso_username_id_map"],
        setup_mock_aws_environment["sso_group_name_id_map"],
        setup_mock_aws_environment["sso_permission_set_name_id_map"],
    )
    expected_account_assignments.sort(key=sort_keys)

    # Create expected account assignments
    upper_bound_range = int(
        len(expected_account_assignments) * account_assignment_range
    )
    existing_account_assignments = expected_account_assignments[0:upper_bound_range]
    for assignment in existing_account_assignments:
        sso_admin_client.create_account_assignment(**assignment)

    # Act
    identity_center_manager = IdentityCenterManager(
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["identity_store_id"],
    )
    identity_center_manager.manifest_file_rbac_rules = rbac_rules
    identity_center_manager.ou_accounts_map = setup_mock_aws_environment[
        "ou_accounts_map"
    ]
    identity_center_manager.account_name_id_map = setup_mock_aws_environment[
        "account_name_id_map"
    ]
    identity_center_manager.run_access_control_resolver()

    # Assert
    assert expected_account_assignments[upper_bound_range:] == sorted(
        identity_center_manager.assignments_to_create, key=sort_keys
    )


@pytest.mark.parametrize(
    "setup_mock_aws_environment, manifest_filename",
    list(itertools.product(AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)),
    indirect=["setup_mock_aws_environment"],
)
def test_delete_account_assignments(
    sso_admin_client: pytest.fixture,
    setup_mock_aws_environment: pytest.fixture,
    manifest_filename: str,
) -> None:
    """
    Test the deletion of account assignments based on manifest file and environment.

    Test Strategy:
        1. Create initial account assignments
        2. Generate expected account assignments from manifest
        3. Identify assignments to be deleted
        4. Retrieve assignments to be delete via IdentityCenterManager.assignments_to_delete
        property
        5. Compare expected assignments to delete vs generated assignments to delete

    Args:
        sso_admin_client (pytest.fixture): Mock AWS SSO admin client
        setup_mock_aws_environment (pytest.fixture): Fixture with mock AWS environment details
        manifest_filename (str): Path to the manifest file defining RBAC rules

    Asserts:
        Verifies that the assignments to be deleted match the expected
        assignments to delete.
    """
    sort_keys = operator.itemgetter(
        "PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId"
    )
    manifest_file = load_file(manifest_filename)
    rbac_rules = manifest_file.get("rbac_rules", [])

    # Generate expected account assignments
    expected_account_assignments = generate_expected_account_assignments(
        manifest_file,
        setup_mock_aws_environment["ou_accounts_map"],
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["account_name_id_map"],
        setup_mock_aws_environment["sso_username_id_map"],
        setup_mock_aws_environment["sso_group_name_id_map"],
        setup_mock_aws_environment["sso_permission_set_name_id_map"],
    )

    def create_assignments(
        principal_ids: List[str], principal_type: str
    ) -> List[Dict[str, Any]]:
        """
        Creates account assignments for given principal IDs and type.

        Generates account assignments concurrently using ThreadPoolExecutor
        to efficiently create multiple assignments.

        Args:
            principal_ids (List[str]): List of principal identifiers
            principal_type (str): Type of principal (USER or GROUP)

        Returns:
            List[Dict[str, Any]]: List of created account assignments
        """
        assignments = []
        assignments_to_create = list(
            itertools.product(
                principal_ids, [principal_type], sso_permission_set_ids, account_ids
            )
        )

        def create_single_assignment(assignment):
            sso_admin_client.create_account_assignment(
                InstanceArn=setup_mock_aws_environment["identity_store_arn"],
                PermissionSetArn=assignment[2],
                PrincipalId=assignment[0],
                PrincipalType=assignment[1],
                TargetId=assignment[3],
                TargetType="AWS_ACCOUNT",
            )
            return {
                "PrincipalId": assignment[0],
                "PrincipalType": assignment[1],
                "PermissionSetArn": assignment[2],
                "TargetId": assignment[3],
                "TargetType": "AWS_ACCOUNT",
                "InstanceArn": setup_mock_aws_environment["identity_store_arn"],
            }

        with concurrent.futures.ThreadPoolExecutor() as executor:
            assignments = list(
                executor.map(create_single_assignment, assignments_to_create)
            )

        return assignments

    # Create SSO user and group assignments
    sso_permission_set_ids = setup_mock_aws_environment[
        "sso_permission_set_name_id_map"
    ].values()
    account_ids = setup_mock_aws_environment["account_name_id_map"].values()

    sso_user_ids = setup_mock_aws_environment["sso_username_id_map"].values()
    sso_group_ids = setup_mock_aws_environment["sso_group_name_id_map"].values()

    current_account_assignments = create_assignments(
        sso_user_ids, USER_PRINCIPAL_TYPE_LABEL
    )
    current_account_assignments += create_assignments(
        sso_group_ids, GROUP_PRINCIPAL_TYPE_LABEL
    )

    # Act
    identity_center_manager = IdentityCenterManager(
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["identity_store_id"],
    )
    identity_center_manager.manifest_file_rbac_rules = rbac_rules
    identity_center_manager.ou_accounts_map = setup_mock_aws_environment[
        "ou_accounts_map"
    ]
    identity_center_manager.account_name_id_map = setup_mock_aws_environment[
        "account_name_id_map"
    ]
    identity_center_manager.run_access_control_resolver()

    # Assert
    assignments_to_delete = list(
        itertools.filterfalse(
            lambda i: i in expected_account_assignments, current_account_assignments
        )
    )
    assert sorted(assignments_to_delete, key=sort_keys) == sorted(
        identity_center_manager.assignments_to_delete, key=sort_keys
    )


@pytest.mark.parametrize(
    "setup_mock_aws_environment, manifest_filename",
    list(itertools.product(AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)),
    indirect=["setup_mock_aws_environment"],
)
def test_generate_invalid_assignments_report(
    setup_mock_aws_environment: pytest.fixture, manifest_filename: str
) -> None:
    """
    Generate and validate a report of invalid account assignments.

    Verifies the IdentityCenterManager's ability to identify and report
    invalid assignments by checking:
        - Invalid target names (OUs or accounts)
        - Invalid principal names (users or groups)
        - Invalid permission set names

    Args:
        setup_mock_aws_environment (pytest.fixture): Fixture with mock AWS environment details
        manifest_filename (str): Path to the manifest file defining RBAC rules

    Asserts:
        Verifies that the generated invalid assignments report matches
        the expected invalid assignments.
    """
    sort_keys = operator.itemgetter(
        "rule_number",
        "resource_type",
        "resource_name",
        "resource_invalid_error_message",
    )
    manifest_file = load_file(manifest_filename)
    rbac_rules = manifest_file.get("rbac_rules", [])

    # Act
    identity_center_manager = IdentityCenterManager(
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["identity_store_id"],
    )
    identity_center_manager.manifest_file_rbac_rules = rbac_rules
    identity_center_manager.ou_accounts_map = setup_mock_aws_environment[
        "ou_accounts_map"
    ]
    identity_center_manager.account_name_id_map = setup_mock_aws_environment[
        "account_name_id_map"
    ]
    identity_center_manager.run_access_control_resolver()

    # Generate invalid assignments report
    invalid_assignments = []
    for i, rule in enumerate(rbac_rules):
        # Check target names
        target_reference = (
            list(setup_mock_aws_environment["ou_accounts_map"].keys())
            if rule["target_type"] == "OU"
            else setup_mock_aws_environment["account_name_id_map"].keys()
        )
        for target_name in rule["target_names"]:
            if target_name not in target_reference:
                invalid_rule = InvalidAssignmentRule(
                    rule_number=i,
                    resource_type=rule["target_type"],
                    resource_name=target_name,
                    resource_invalid_error_message=f"Invalid {rule['target_type']} - resource with name ({target_name}) not found",
                    resource_invalid_error_code=f"INVALID_{rule['target_type']}_NAME",
                )
                invalid_assignments.append(invalid_rule.to_dict())

        # Check principal name
        principal_reference = (
            setup_mock_aws_environment["sso_group_name_id_map"].keys()
            if rule["principal_type"] == "GROUP"
            else setup_mock_aws_environment["sso_username_id_map"]
        )
        if rule["principal_name"] not in principal_reference:
            invalid_rule = InvalidAssignmentRule(
                rule_number=i,
                resource_type=rule["principal_type"],
                resource_name=rule["principal_name"],
                resource_invalid_error_message=f"Invalid SSO {rule['principal_type']} - resource with name ({rule["principal_name"]}) not found",
                resource_invalid_error_code=f"INVALID_SSO_{rule['principal_type']}_NAME",
            )
            invalid_assignments.append(invalid_rule.to_dict())

        # Check permission set name
        if (
            rule["permission_set_name"]
            not in setup_mock_aws_environment["sso_permission_set_name_id_map"]
        ):
            invalid_rule = InvalidAssignmentRule(
                rule_number=i,
                resource_type=PERMISSION_SET_TYPE_LABEL,
                resource_name=rule["permission_set_name"],
                resource_invalid_error_message=f"Invalid {PERMISSION_SET_TYPE_LABEL} - resource with name ({rule['permission_set_name']}) not found",
                resource_invalid_error_code=f"INVALID_{PERMISSION_SET_TYPE_LABEL}_NAME",
            )
            invalid_assignments.append(invalid_rule.to_dict())

    # Assert
    assert sorted(invalid_assignments, key=sort_keys) == sorted(
        identity_center_manager.invalid_assignments_report, key=sort_keys
    )
