"""
Unit tests for an AWS Lambda function using moto to mock S3 interactions.

This module contains helper functions and test cases for the Lambda function.
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

# Constants
CWD = os.path.dirname(os.path.realpath(__file__))
PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES = [round(i * 0.2, 2) for i in range(6)]  # 20% increments

AWS_ORG_DEFINITIONS_FILES_PATH = os.path.join(CWD, "..", "configs", "organizations", "*.json")
AWS_ORG_DEFINITION_FILES = [os.path.basename(x) for x in glob.glob(AWS_ORG_DEFINITIONS_FILES_PATH)]

VALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(CWD, "..", "manifests", "valid_schema", "*.yaml")
VALID_MANIFEST_DEFINITION_FILES = [os.path.abspath(x) for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)]


def create_assignments(
    sso_admin_client: boto3.client,
    setup_mock_aws_environment: Dict[str, Any],
    principal_ids: List[str],
    principal_type: str,
    sso_permission_set_ids: List[str],
    account_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Creates account assignments for the given principal IDs and principal type.

    Args:
        sso_admin_client (boto3.client): The boto3 SSO admin client.
        setup_mock_aws_environment (Dict[str, Any]): The AWS environment setup.
        principal_ids (List[str]): List of principal IDs.
        principal_type (str): Principal type (USER or GROUP).
        sso_permission_set_ids (List[str]): List of SSO permission set IDs.
        account_ids (List[str]): List of account IDs.

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


def generate_invalid_assignments(manifest_file: Dict[str, Any], setup_mock_aws_environment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates a list of invalid assignments from the manifest file.

    Args:
        manifest_file (Dict[str, Any]): The manifest file.
        setup_mock_aws_environment (Dict[str, Any]): The AWS environment setup.

    Returns:
        List[Dict[str, Any]]: List of invalid assignments.
    """
    invalid_assignments = []
    rbac_rules = manifest_file.get("rbac_rules", [])
    for i, rule in enumerate(rbac_rules):
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

        principal_reference = setup_mock_aws_environment["sso_group_name_id_map"].keys() if rule["principal_type"] == "GROUP" else setup_mock_aws_environment["sso_username_id_map"]
        if rule["principal_name"] not in principal_reference:
            invalid_assignments.append(
                {
                    "rule_number": i,
                    "resource_type": rule["principal_type"],
                    "resource_name": rule["principal_name"],
                }
            )

        if rule["permission_set_name"] not in setup_mock_aws_environment["sso_permission_set_name_id_map"]:
            invalid_assignments.append(
                {
                    "rule_number": i,
                    "resource_type": "permission_set",
                    "resource_name": rule["permission_set_name"],
                }
            )
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
    Test the main function with a mocked S3 environment.

    This test verifies that the main function correctly processes a
    manifest file uploaded to an S3 bucket and creates the expected AWS SSO
    account assignments based on the provided environment setup.

    Parameters:
    ----------
    sso_admin_client : boto3.client
        The boto3 SSO admin client.
    account_assignment_range : float
        The percentage range of account assignments to pre-create.
    setup_mock_aws_environment : Dict[str, Any]
        The AWS environment setup.
    manifest_filepath : str
        The filename of the manifest to be tested.
    """
    invalid_assignments_report_sort_keys = operator.itemgetter("rule_number", "resource_type", "resource_name")
    created_assignments_sort_keys = operator.itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
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

    upper_bound_range = int(len(expected_account_assignments) * account_assignment_range)
    current_account_assignments = expected_account_assignments[:upper_bound_range]
    for assignment in current_account_assignments:
        sso_admin_client.create_account_assignment(**assignment)

    invalid_assignments = generate_invalid_assignments(manifest_file, setup_mock_aws_environment)

    from src.cli import sso  # pylint: disable=C0415

    importlib.reload(sso)

    cli_results = sso.create_sso_assignments(
        manifest_filepath,
        True,
    )

    assert expected_account_assignments[upper_bound_range:] == sorted(cli_results["created"], key=created_assignments_sort_keys)
    assert sorted(invalid_assignments, key=invalid_assignments_report_sort_keys) == sorted(cli_results["invalid"], key=invalid_assignments_report_sort_keys)


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
    This test verifies that the main function correctly processes a
    manifest file uploaded to an S3 bucket and deletes
    Parameters:
    ----------
    sso_admin_client : boto3.client
        The boto3 SSO admin client.
    setup_mock_aws_environment : Dict[str, Any]
        The AWS environment setup.
    manifest_filepath : str
        The filename of the manifest to be tested.
    """
    sort_keys = operator.itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
    manifest_definition_filepath = os.path.join(CWD, "configs", "manifests", "valid_schema", manifest_filepath)

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

    sso_permission_set_ids = setup_mock_aws_environment["sso_permission_set_name_id_map"].values()
    account_ids = setup_mock_aws_environment["account_name_id_map"].values()

    sso_user_ids = setup_mock_aws_environment["sso_username_id_map"].values()
    sso_group_ids = setup_mock_aws_environment["sso_group_name_id_map"].values()

    current_account_assignments = create_assignments(
        sso_admin_client,
        setup_mock_aws_environment,
        list(sso_user_ids),
        "USER",
        list(sso_permission_set_ids),
        list(account_ids),
    )
    current_account_assignments += create_assignments(
        sso_admin_client,
        setup_mock_aws_environment,
        list(sso_group_ids),
        "GROUP",
        list(sso_permission_set_ids),
        list(account_ids),
    )

    from src.cli import sso  # pylint: disable=C0415

    importlib.reload(sso)

    cli_results = sso.create_sso_assignments(
        manifest_filepath,
        True,
    )

    assignments_to_delete = list(itertools.filterfalse(lambda i: i in expected_account_assignments, current_account_assignments))
    assert sorted(assignments_to_delete, key=sort_keys) == sorted(cli_results["deleted"], key=sort_keys)
