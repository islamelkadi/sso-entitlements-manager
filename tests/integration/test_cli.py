"""
Unit Tests for AWS SSO Account Assignment Management

This module provides comprehensive test cases for AWS SSO account assignment
management, focusing on:
    - Verifying SSO account assignment creation
    - Validating assignment generation logic
    - Testing assignment deletion processes

The tests leverage moto for mocking AWS environments and support:
    - Parametrized testing across multiple organization configurations
    - Validation of account assignments against manifest files
    - Handling of valid and invalid assignment scenarios

Key Testing Strategies:
    - Dynamic generation of test scenarios
    - Concurrent assignment creation
    - Comprehensive coverage of assignment lifecycles

Dependencies:
    - pytest: Test framework
    - boto3: AWS SDK
    - moto: AWS service mocking
    - concurrent.futures: Parallel test execution support

Note:
    Test configurations are dynamically loaded from '../configs' and
    '../manifests' directories.
"""

import os
import glob
import operator
import itertools
import importlib
import concurrent.futures
from typing import Any, Dict, List

import boto3
import pytest
from tests.utils import (
    generate_expected_account_assignments,
)
from src.core.utils import load_file
from src.core.constants import (
    GROUP_PRINCIPAL_TYPE_LABEL,
    USER_PRINCIPAL_TYPE_LABEL,
    PERMISSION_SET_TYPE_LABEL,
    OU_TARGET_TYPE_LABEL,
)
from src.services.aws.aws_identity_center_manager import InvalidAssignmentRule

# Constants
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


def create_assignments(
    sso_admin_client: boto3.client,
    setup_mock_aws_environment: Dict[str, Any],
    principal_ids: List[str],
    principal_type: str,
    sso_permission_set_ids: List[str],
    account_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Create AWS SSO account assignments using concurrent execution.

    This function generates account assignments by creating combinations of
    principals, permission sets, and accounts. It uses a thread pool executor
    to parallelize assignment creation for improved performance.

    Args:
        sso_admin_client (boto3.client): Boto3 SSO admin client for API calls.
        setup_mock_aws_environment (Dict[str, Any]): Mocked AWS environment configuration.
        principal_ids (List[str]): List of principal (user/group) IDs to assign.
        principal_type (str): Type of principal - 'USER' or 'GROUP'.
        sso_permission_set_ids (List[str]): List of SSO permission set IDs.
        account_ids (List[str]): List of target AWS account IDs.

    Returns:
        List[Dict[str, Any]]: Comprehensive list of created account assignments.

    Strategy:
        - Generate all possible assignment combinations
        - Use ThreadPoolExecutor for parallel assignment creation
        - Capture and return detailed assignment metadata
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


def generate_invalid_assignments(
    manifest_file: Dict[str, Any], setup_mock_aws_environment: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Identify invalid assignments from a manifest file.

    This function validates the manifest file against the mock AWS environment,
    detecting inconsistencies in:
        - Target resources (OUs or accounts)
        - Principal references (users or groups)
        - Permission set configurations

    Args:
        manifest_file (Dict[str, Any]): Parsed manifest file configuration.
        setup_mock_aws_environment (Dict[str, Any]): Mocked AWS environment configuration.

    Returns:
        List[Dict[str, Any]]: List of invalid assignments with detailed error information.

    Validation Checks:
        - Verify target resource existence
        - Confirm principal references
        - Validate permission set configurations
    """
    invalid_assignments = []
    rbac_rules = manifest_file.get("rbac_rules", [])
    for i, rule in enumerate(rbac_rules):
        # Check target names
        target_reference = (
            list(setup_mock_aws_environment["ou_accounts_map"].keys())
            if rule["target_type"] == OU_TARGET_TYPE_LABEL
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
            if rule["principal_type"] == GROUP_PRINCIPAL_TYPE_LABEL
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
    return invalid_assignments


@pytest.mark.parametrize(
    "account_assignment_range, setup_mock_aws_environment, manifest_filepath",
    list(
        itertools.product(
            PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES,
            AWS_ORG_DEFINITION_FILES,
            VALID_MANIFEST_DEFINITION_FILES,
        )
    ),
    indirect=["setup_mock_aws_environment"],
)
def test_main(
    sso_admin_client: boto3.client,
    account_assignment_range: float,
    setup_mock_aws_environment: Dict[str, Any],
    manifest_filepath: str,
) -> None:
    """
    Comprehensive test for SSO account assignment creation and management.

    This test verifies the end-to-end process of creating SSO account assignments
    based on a manifest file. It supports incremental assignment creation and
    validates the completeness of assignment generation.

    Key Test Objectives:
        - Generate expected account assignments
        - Pre-create a subset of assignments
        - Verify remaining assignments are correctly created
        - Validate handling of invalid assignments

    Args:
        sso_admin_client (boto3.client): Boto3 SSO admin client for API interactions.
        account_assignment_range (float): Percentage of pre-existing assignments (0.0 to 1.0).
        setup_mock_aws_environment (Dict[str, Any]): Mocked AWS environment configuration.
        manifest_filepath (str): Path to the manifest file defining assignment rules.

    Test Strategy:
        - Load manifest file
        - Generate expected account assignments
        - Pre-create partial assignments based on range
        - Execute SSO assignment creation
        - Assert newly created and invalid assignments match expectations
    """
    invalid_assignments_report_sort_keys = operator.itemgetter(
        "rule_number",
        "resource_type",
        "resource_name",
        "resource_invalid_error_message",
    )
    created_assignments_sort_keys = operator.itemgetter(
        "PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId"
    )
    manifest_file = load_file(manifest_filepath)

    expected_account_assignments = generate_expected_account_assignments(
        manifest_file,
        setup_mock_aws_environment["ou_accounts_map"],
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["account_name_id_map"],
        setup_mock_aws_environment["sso_username_id_map"],
        setup_mock_aws_environment["sso_group_name_id_map"],
        setup_mock_aws_environment["sso_permission_set_name_id_map"],
    )
    expected_account_assignments.sort(key=created_assignments_sort_keys)

    upper_bound_range = int(
        len(expected_account_assignments) * account_assignment_range
    )
    current_account_assignments = expected_account_assignments[:upper_bound_range]
    for assignment in current_account_assignments:
        sso_admin_client.create_account_assignment(**assignment)

    invalid_assignments = generate_invalid_assignments(
        manifest_file, setup_mock_aws_environment
    )

    from src.cli import sso  # pylint: disable=C0415

    importlib.reload(sso)

    cli_results = sso.create_sso_assignments(
        manifest_filepath,
        True,
    )

    assert expected_account_assignments[upper_bound_range:] == sorted(
        cli_results["created"], key=created_assignments_sort_keys
    )
    assert sorted(
        invalid_assignments, key=invalid_assignments_report_sort_keys
    ) == sorted(cli_results["invalid"], key=invalid_assignments_report_sort_keys)


@pytest.mark.parametrize(
    "setup_mock_aws_environment, manifest_filepath",
    list(itertools.product(AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)),
    indirect=["setup_mock_aws_environment"],
)
def test_delete(
    sso_admin_client: boto3.client,
    setup_mock_aws_environment: Dict[str, Any],
    manifest_filepath: str,
) -> None:
    """
    Test SSO account assignment deletion process.

    Validates the correct removal of existing account assignments that
    are no longer defined in the manifest file.

    Key Test Objectives:
        - Create comprehensive set of initial assignments
        - Execute assignment synchronization
        - Verify assignments not in manifest are deleted

    Args:
        sso_admin_client (boto3.client): Boto3 SSO admin client for API interactions.
        setup_mock_aws_environment (Dict[str, Any]): Mocked AWS environment configuration.
        manifest_filepath (str): Path to the manifest file defining current assignment rules.

    Test Strategy:
        - Generate all possible account assignments
        - Create initial set of assignments
        - Execute SSO assignment synchronization
        - Assert deleted assignments match expectations
    """
    sort_keys = operator.itemgetter(
        "PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId"
    )
    manifest_definition_filepath = os.path.join(
        CWD, "configs", "manifests", "valid_schema", manifest_filepath
    )

    manifest_file = load_file(manifest_definition_filepath)

    expected_account_assignments = generate_expected_account_assignments(
        manifest_file,
        setup_mock_aws_environment["ou_accounts_map"],
        setup_mock_aws_environment["identity_store_arn"],
        setup_mock_aws_environment["account_name_id_map"],
        setup_mock_aws_environment["sso_username_id_map"],
        setup_mock_aws_environment["sso_group_name_id_map"],
        setup_mock_aws_environment["sso_permission_set_name_id_map"],
    )

    sso_permission_set_ids = setup_mock_aws_environment[
        "sso_permission_set_name_id_map"
    ].values()
    account_ids = setup_mock_aws_environment["account_name_id_map"].values()

    sso_user_ids = setup_mock_aws_environment["sso_username_id_map"].values()
    sso_group_ids = setup_mock_aws_environment["sso_group_name_id_map"].values()

    current_account_assignments = create_assignments(
        sso_admin_client,
        setup_mock_aws_environment,
        list(sso_user_ids),
        USER_PRINCIPAL_TYPE_LABEL,
        list(sso_permission_set_ids),
        list(account_ids),
    )
    current_account_assignments += create_assignments(
        sso_admin_client,
        setup_mock_aws_environment,
        list(sso_group_ids),
        GROUP_PRINCIPAL_TYPE_LABEL,
        list(sso_permission_set_ids),
        list(account_ids),
    )

    from src.cli import sso  # pylint: disable=C0415

    importlib.reload(sso)

    cli_results = sso.create_sso_assignments(
        manifest_filepath,
        True,
    )

    assignments_to_delete = list(
        itertools.filterfalse(
            lambda i: i in expected_account_assignments, current_account_assignments
        )
    )
    assert sorted(assignments_to_delete, key=sort_keys) == sorted(
        cli_results["deleted"], key=sort_keys
    )
