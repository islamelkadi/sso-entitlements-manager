import os
import glob
import operator
import itertools
import concurrent.futures
from typing import Dict, List, Set, Tuple, Any

import pytest
from .utils import generate_expected_account_assignments
from app.lib.utils import load_file
from app.lib.access_control_resolver import AwsAccessResolver


# Globals vars
CWD = os.path.dirname(os.path.realpath(__file__))

PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES = [round(i * 0.2, 2) for i in range(6)]  # 20% increments

AWS_ORG_DEFINITIONS_FILES_PATH = os.path.join(CWD, "..", "configs", "organizations", "*.json")
AWS_ORG_DEFINITION_FILES = [os.path.basename(x) for x in glob.glob(AWS_ORG_DEFINITIONS_FILES_PATH)]

VALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(CWD, "..", "configs", "manifests", "valid_schema", "*.yaml")
VALID_MANIFEST_DEFINITION_FILES = [os.path.basename(x) for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)]


# Test cases
@pytest.mark.parametrize(
    "account_assignment_range, setup_aws_environment, manifest_filename",
    list(itertools.product(PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES, AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)),
    indirect=["setup_aws_environment"]
)
def test_create_assignments(sso_admin_client, account_assignment_range: float, setup_aws_environment: pytest.fixture, manifest_filename: str) -> None:

    #########################
    #         Arrange       #
    #########################

    sort_keys = operator.itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
    manifest_file = load_file(os.path.join(CWD, "..", "configs", "manifests", "valid_schema", manifest_filename))
    rbac_rules = manifest_file.get("rbac_rules", [])

    # Generate expected account assignments
    expected_account_assignments = generate_expected_account_assignments(
        manifest_file,
        setup_aws_environment["ou_accounts_map"],
        setup_aws_environment["account_name_id_map"],
        setup_aws_environment["sso_username_id_map"],
        setup_aws_environment["sso_group_name_id_map"],
        setup_aws_environment["sso_permission_set_name_id_map"],
    )
    expected_account_assignments.sort(key=sort_keys)

    # Create expected account assignments
    upper_bound_range = int(len(expected_account_assignments) * account_assignment_range)
    existing_account_assignments = expected_account_assignments[0:upper_bound_range]
    for assignment in existing_account_assignments:
        sso_admin_client.create_account_assignment(**assignment)

    #########################
    #           Act         #
    #########################

    aws_access_resolver = AwsAccessResolver(setup_aws_environment["identity_center_arn"])
    setattr(aws_access_resolver, "rbac_rules", rbac_rules)
    setattr(aws_access_resolver, "sso_users", setup_aws_environment["sso_username_id_map"])
    setattr(aws_access_resolver, "sso_groups", setup_aws_environment["sso_group_name_id_map"])
    setattr(aws_access_resolver, "permission_sets", setup_aws_environment["sso_permission_set_name_id_map"])
    setattr(aws_access_resolver, "ou_accounts_map", setup_aws_environment["ou_accounts_map"])
    setattr(aws_access_resolver, "account_name_id_map", setup_aws_environment["account_name_id_map"])
    aws_access_resolver.run_access_control_resolver()

    #########################
    #         Assert        #
    #########################

    # Assert expected assignment to create matches actual created assignments
    assert expected_account_assignments[upper_bound_range:] == sorted(aws_access_resolver.assignments_to_create, key=sort_keys)


@pytest.mark.parametrize("setup_aws_environment, manifest_filename", list(itertools.product(AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)), indirect=["setup_aws_environment"])
def test_generate_invalid_assignments_report(setup_aws_environment: pytest.fixture, manifest_filename: str) -> None:

    #########################
    #         Arrange       #
    #########################

    sort_keys = operator.itemgetter("rule_number", "resource_type", "resource_name")
    manifest_file = load_file(os.path.join(CWD, "..", "configs", "manifests", "valid_schema", manifest_filename))
    rbac_rules = manifest_file.get("rbac_rules", [])

    #########################
    #           Act         #
    #########################

    ################# Run access control resolver #################
    aws_access_resolver = AwsAccessResolver(setup_aws_environment["identity_center_arn"])
    setattr(aws_access_resolver, "rbac_rules", rbac_rules)
    setattr(aws_access_resolver, "sso_users", setup_aws_environment["sso_username_id_map"])
    setattr(aws_access_resolver, "sso_groups", setup_aws_environment["sso_group_name_id_map"])
    setattr(aws_access_resolver, "permission_sets", setup_aws_environment["sso_permission_set_name_id_map"])
    setattr(aws_access_resolver, "ou_accounts_map", setup_aws_environment["ou_accounts_map"])
    setattr(aws_access_resolver, "account_name_id_map", setup_aws_environment["account_name_id_map"])
    aws_access_resolver.run_access_control_resolver()

    ############# Generate invalid assignments report #############
    invalid_assignments = []
    for i, rule in enumerate(rbac_rules):
        # Check target names
        target_reference = list(setup_aws_environment["ou_accounts_map"].keys()) if rule["target_type"] == "OU" else setup_aws_environment["account_name_id_map"].keys()
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
        target_reference = setup_aws_environment["sso_group_name_id_map"].keys() if rule["principal_type"] == "GROUP" else setup_aws_environment["sso_username_id_map"]
        if rule["principal_name"] not in target_reference:
            invalid_assignments.append(
                {
                    "rule_number": i,
                    "resource_type": rule["principal_type"],
                    "resource_name": rule["principal_name"],
                }
            )

        # Check permission set name
        if rule["permission_set_name"] not in setup_aws_environment["sso_permission_set_name_id_map"]:
            invalid_assignments.append(
                {
                    "rule_number": i,
                    "resource_type": "permission_set",
                    "resource_name": rule["permission_set_name"],
                }
            )

    #########################
    #         Assert        #
    #########################

    # Assert test generated invalid report matches class generated invalid report matches
    assert sorted(invalid_assignments, key=sort_keys) == sorted(aws_access_resolver.invalid_manifest_rules_report, key=sort_keys)


@pytest.mark.parametrize("setup_aws_environment, manifest_filename", list(itertools.product(AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)), indirect=["setup_aws_environment"])
def test_delete_account_assignments(sso_admin_client: pytest.fixture, setup_aws_environment: pytest.fixture, manifest_filename: str) -> None:

    #########################
    #         Arrange       #
    #########################

    sort_keys = operator.itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
    manifest_file = load_file(os.path.join(CWD, "..", "configs", "manifests", "valid_schema", manifest_filename))
    rbac_rules = manifest_file.get("rbac_rules", [])

    # Generate expected account assignments
    expected_account_assignments = generate_expected_account_assignments(
        manifest_file,
        setup_aws_environment["ou_accounts_map"],
        setup_aws_environment["account_name_id_map"],
        setup_aws_environment["sso_username_id_map"],
        setup_aws_environment["sso_group_name_id_map"],
        setup_aws_environment["sso_permission_set_name_id_map"],
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
            sso_admin_client.create_account_assignment(InstanceArn=setup_aws_environment["identity_center_arn"], PermissionSetArn=assignment[2], PrincipalId=assignment[0], PrincipalType=assignment[1], TargetId=assignment[3], TargetType="AWS_ACCOUNT")
            return {"PrincipalId": assignment[0], "PrincipalType": assignment[1], "PermissionSetArn": assignment[2], "TargetId": assignment[3], "TargetType": "AWS_ACCOUNT", "InstanceArn": setup_aws_environment["identity_center_arn"]}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            assignments = list(executor.map(create_single_assignment, assignments_to_create))

        return assignments

    # Create SSO user and group assignments
    sso_permission_set_ids = setup_aws_environment["sso_permission_set_name_id_map"].values()
    account_ids = setup_aws_environment["account_name_id_map"].values()

    sso_user_ids = setup_aws_environment["sso_username_id_map"].values()
    sso_group_ids = setup_aws_environment["sso_group_name_id_map"].values()

    current_account_assignments = create_assignments(sso_user_ids, "USER")
    current_account_assignments += create_assignments(sso_group_ids, "GROUP")

    #########################
    #           Act         #
    #########################

    aws_access_resolver = AwsAccessResolver(setup_aws_environment["identity_center_arn"])
    setattr(aws_access_resolver, "rbac_rules", rbac_rules)
    setattr(aws_access_resolver, "sso_users", setup_aws_environment["sso_username_id_map"])
    setattr(aws_access_resolver, "sso_groups", setup_aws_environment["sso_group_name_id_map"])
    setattr(aws_access_resolver, "permission_sets", setup_aws_environment["sso_permission_set_name_id_map"])
    setattr(aws_access_resolver, "ou_accounts_map", setup_aws_environment["ou_accounts_map"])
    setattr(aws_access_resolver, "account_name_id_map", setup_aws_environment["account_name_id_map"])
    aws_access_resolver.run_access_control_resolver()

    #########################
    #         Assert        #
    #########################

    assignments_to_delete = list(itertools.filterfalse(lambda i: i in expected_account_assignments, current_account_assignments))
    assert sorted(assignments_to_delete, key=sort_keys) == sorted(aws_access_resolver.assignments_to_delete, key=sort_keys)
