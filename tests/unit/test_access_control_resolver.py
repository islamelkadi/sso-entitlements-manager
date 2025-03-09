"""
Unit tests for the SsoAdminManager class.

This module contains tests for the AWS Access Control Resolver, verifying the creation,
deletion, and reporting of account assignments based on the provided manifest files and
AWS environment setup. The tests utilize pytest for parameterization and fixtures for
mocking AWS resources.

Functions:
    test_create_assignments: Test the creation of account assignments.
    test_generate_invalid_assignments_report: Test the generation of a report for invalid assignments.
    test_delete_account_assignments: Test the deletion of account assignments.
"""
import os
import glob
import operator
import itertools
import concurrent.futures
from typing import Dict, List, Any

import pytest
from src.core.utils import load_file
from src.services.aws.access_control_resolver import SsoAdminManager
from tests.utils import generate_expected_account_assignments

# Globals vars
CWD = os.path.dirname(os.path.realpath(__file__))

PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES = [round(i * 0.2, 2) for i in range(6)]  # 20% increments

AWS_ORG_DEFINITIONS_FILES_PATH = os.path.join(CWD, "..", "configs", "organizations", "*.json")
AWS_ORG_DEFINITION_FILES = [os.path.basename(x) for x in glob.glob(AWS_ORG_DEFINITIONS_FILES_PATH)]

VALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(CWD, "..", "manifests", "valid_schema", "*.yaml")
VALID_MANIFEST_DEFINITION_FILES = [os.path.abspath(x) for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)]


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
    Test the creation of account assignments based on the provided manifest file and setup environment.

    Args:
        sso_admin_client: Mock AWS SSO admin client.
        account_assignment_range (float): Percentage of assignments to pre-create.
        setup_mock_aws_environment (pytest.fixture): Fixture setting up the AWS test environment.
        manifest_filename (str): Filename of the manifest file to be loaded.

    Asserts:
        Verifies that the assignments created match the expected assignments.
    """
    sort_keys = operator.itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
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
    upper_bound_range = int(len(expected_account_assignments) * account_assignment_range)
    existing_account_assignments = expected_account_assignments[0:upper_bound_range]
    for assignment in existing_account_assignments:
        sso_admin_client.create_account_assignment(**assignment)

    # Act
    identity_center_manager = SsoAdminManager(setup_mock_aws_environment["identity_store_arn"])
    setattr(
        identity_center_manager,
        "manifest_file_rbac_rules",
        rbac_rules
    )
    setattr(
        identity_center_manager,
        "sso_users",
        setup_mock_aws_environment["sso_username_id_map"],
    )
    setattr(
        identity_center_manager,
        "sso_groups",
        setup_mock_aws_environment["sso_group_name_id_map"],
    )
    setattr(
        identity_center_manager,
        "sso_permission_sets",
        setup_mock_aws_environment["sso_permission_set_name_id_map"],
    )
    setattr(
        identity_center_manager,
        "ou_accounts_map",
        setup_mock_aws_environment["ou_accounts_map"],
    )
    setattr(
        identity_center_manager,
        "account_name_id_map",
        setup_mock_aws_environment["account_name_id_map"],
    )
    identity_center_manager.run_access_control_resolver()

    # Assert
    assert expected_account_assignments[upper_bound_range:] == sorted(identity_center_manager.assignments_to_create, key=sort_keys)


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
    Test the deletion of account assignments based on the provided manifest file and setup environment.

    Args:
        sso_admin_client (pytest.fixture): Mock AWS SSO admin client.
        setup_mock_aws_environment (pytest.fixture): Fixture setting up the AWS test environment.
        manifest_filename (str): Filename of the manifest file to be loaded.

    Asserts:
        Verifies that the assignments to be deleted match the expected assignments to delete.
    """
    sort_keys = operator.itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
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

    def create_assignments(principal_ids: List[str], principal_type: str) -> List[Dict[str, Any]]:
        """
        Creates account assignments for the given principal IDs and principal type.

        Args:
            principal_ids (List[str]): List of principal IDs.
            principal_type (str): Principal type (USER or GROUP).

        Returns:
            List[Dict[str, Any]]: List of created account assignments.
        """
        assignments = []
        assignments_to_create = list(itertools.product(principal_ids, [principal_type], sso_permission_set_ids, account_ids))

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
            assignments = list(executor.map(create_single_assignment, assignments_to_create))

        return assignments

    # Create SSO user and group assignments
    sso_permission_set_ids = setup_mock_aws_environment["sso_permission_set_name_id_map"].values()
    account_ids = setup_mock_aws_environment["account_name_id_map"].values()

    sso_user_ids = setup_mock_aws_environment["sso_username_id_map"].values()
    sso_group_ids = setup_mock_aws_environment["sso_group_name_id_map"].values()

    current_account_assignments = create_assignments(sso_user_ids, "USER")
    current_account_assignments += create_assignments(sso_group_ids, "GROUP")

    # Act
    identity_center_manager = SsoAdminManager(setup_mock_aws_environment["identity_store_arn"])
    setattr(identity_center_manager, "manifest_file_rbac_rules", rbac_rules)
    setattr(
        identity_center_manager,
        "sso_users",
        setup_mock_aws_environment["sso_username_id_map"],
    )
    setattr(
        identity_center_manager,
        "sso_groups",
        setup_mock_aws_environment["sso_group_name_id_map"],
    )
    setattr(
        identity_center_manager,
        "sso_permission_sets",
        setup_mock_aws_environment["sso_permission_set_name_id_map"],
    )
    setattr(
        identity_center_manager,
        "ou_accounts_map",
        setup_mock_aws_environment["ou_accounts_map"],
    )
    setattr(
        identity_center_manager,
        "account_name_id_map",
        setup_mock_aws_environment["account_name_id_map"],
    )
    identity_center_manager.run_access_control_resolver()

    # Assert
    assignments_to_delete = list(itertools.filterfalse(lambda i: i in expected_account_assignments, current_account_assignments))
    assert sorted(assignments_to_delete, key=sort_keys) == sorted(identity_center_manager.assignments_to_delete, key=sort_keys)


@pytest.mark.parametrize(
    "setup_mock_aws_environment, manifest_filename",
    list(itertools.product(AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)),
    indirect=["setup_mock_aws_environment"],
)
def test_generate_invalid_assignments_report(setup_mock_aws_environment: pytest.fixture, manifest_filename: str) -> None:
    """
    Test the generation of a report for invalid account assignments based on the provided manifest file and setup environment.

    Args:
        setup_mock_aws_environment (pytest.fixture): Fixture setting up the AWS test environment.
        manifest_filename (str): Filename of the manifest file to be loaded.

    Asserts:
        Verifies that the generated invalid assignments report matches the expected invalid assignments.
    """
    sort_keys = operator.itemgetter("rule_number", "resource_type", "resource_name")
    manifest_file = load_file(manifest_filename)
    rbac_rules = manifest_file.get("rbac_rules", [])

    # Act
    identity_center_manager = SsoAdminManager(setup_mock_aws_environment["identity_store_arn"])
    setattr(identity_center_manager, "manifest_file_rbac_rules", rbac_rules)
    setattr(
        identity_center_manager,
        "sso_users",
        setup_mock_aws_environment["sso_username_id_map"],
    )
    setattr(
        identity_center_manager,
        "sso_groups",
        setup_mock_aws_environment["sso_group_name_id_map"],
    )
    setattr(
        identity_center_manager,
        "sso_permission_sets",
        setup_mock_aws_environment["sso_permission_set_name_id_map"],
    )
    setattr(
        identity_center_manager,
        "ou_accounts_map",
        setup_mock_aws_environment["ou_accounts_map"],
    )
    setattr(
        identity_center_manager,
        "account_name_id_map",
        setup_mock_aws_environment["account_name_id_map"],
    )
    identity_center_manager.run_access_control_resolver()

    # Generate invalid assignments report
    invalid_assignments = []
    for i, rule in enumerate(rbac_rules):
        # Check target names
        target_reference = list(setup_mock_aws_environment["ou_accounts_map"].keys()) if rule["target_type"] == "OU" else setup_mock_aws_environment["account_name_id_map"].keys()
        for target_name in rule["target_names"]:
            if target_name not in target_reference:
                invalid_assignments.append(
                    {
                        "rule_number": i,
                        "resource_type": rule["target_type"],
                        "resource_name": target_name,
                    }
                )

        # Check principal name
        target_reference = setup_mock_aws_environment["sso_group_name_id_map"].keys() if rule["principal_type"] == "GROUP" else setup_mock_aws_environment["sso_username_id_map"]
        if rule["principal_name"] not in target_reference:
            invalid_assignments.append(
                {
                    "rule_number": i,
                    "resource_type": rule["principal_type"],
                    "resource_name": rule["principal_name"],
                }
            )

        # Check permission set name
        if rule["permission_set_name"] not in setup_mock_aws_environment["sso_permission_set_name_id_map"]:
            invalid_assignments.append(
                {
                    "rule_number": i,
                    "resource_type": "permission_set",
                    "resource_name": rule["permission_set_name"],
                }
            )

    # Assert
    assert sorted(invalid_assignments, key=sort_keys) == sorted(identity_center_manager.invalid_assignments_report, key=sort_keys)
