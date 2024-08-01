"""
Unit tests for an AWS Lambda function using moto to mock S3 interactions.

This module contains helper functions and test cases for the Lambda function.
"""

# Imports
import os
import glob
import operator
import itertools
import importlib

import boto3
import pytest
from .utils import generate_expected_account_assignments
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from app.lib.utils import generate_lambda_context, upload_file_to_s3, load_file

# S3 bucket and object names
BUCKET_NAME = "my-test-bucket"
CWD = os.path.dirname(os.path.realpath(__file__))
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(
    CWD,
    "..",
    "..",
    "src",
    "app",
    "schemas",
    "manifest_schema_definition.json",
)

# Constants
PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES = [round(1 * 0.2, 2) for i in range(1)]  # 20% increments

AWS_ORG_DEFINITIONS_FILES_PATH = os.path.join(CWD, "..", "configs", "organizations", "*.json")
AWS_ORG_DEFINITION_FILES = [os.path.basename(x) for x in glob.glob(AWS_ORG_DEFINITIONS_FILES_PATH)]

VALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(CWD, "..", "configs", "manifests", "valid_schema", "*.yaml")
VALID_MANIFEST_DEFINITION_FILES = [os.path.basename(x) for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)]

# Test cases
@pytest.mark.parametrize(
    "account_assignment_range, setup_aws_environment, manifest_filename",
    list(itertools.product(PRE_TEST_ACCOUNT_ASSIGNMENT_PERCENTAGES, AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)),
    indirect=["setup_aws_environment"],
)
def test_lambda_handler(
    sso_admin_client: pytest.fixture,
    account_assignment_range: float,
    setup_aws_environment: pytest.fixture,  # pylint: disable=W0613
    manifest_filename: str,
) -> None:
    """
    Test the lambda_handler function with a mocked S3 environment.

    This test verifies that the lambda_handler function correctly processes a 
    manifest file uploaded to an S3 bucket and creates the expected AWS SSO 
    account assignments based on the provided environment setup.

    Parameters:
    ----------
    sso_admin_client : pytest.fixture
        The pytest fixture to mock the AWS SSO admin client.
    account_assignment_range : float
        The percentage range of account assignments to pre-create.
    setup_aws_environment : pytest.fixture
        The pytest fixture to set up the AWS environment.
    manifest_filename : str
        The filename of the manifest to be tested.
    """
    #########################
    #         Arrange       #
    #########################

    sort_keys = operator.itemgetter("PermissionSetArn", "PrincipalType", "PrincipalId", "TargetId")
    manifest_definition_filepath = os.path.join(CWD, "..", "configs", "manifests", "valid_schema", manifest_filename)

    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.create_bucket(Bucket=BUCKET_NAME)
    upload_file_to_s3(BUCKET_NAME, manifest_definition_filepath)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("MANIFEST_FILE_S3_LOCATION", f"s3://{BUCKET_NAME}/{manifest_filename}")

    manifest_file = load_file(manifest_definition_filepath)

    #########################
    #           Act         #
    #########################

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

    from src.app import index  # pylint: disable=C0415

    importlib.reload(index)
    lambda_response = index.lambda_handler(EventBridgeEvent(data={}), context=generate_lambda_context())

    #########################
    #         Assert        #
    #########################

    # Assert expected assignment to create matches actual created assignments
    assert sorted(expected_account_assignments[upper_bound_range:], key=sort_keys) == sorted(lambda_response.body["created"], key=sort_keys)
