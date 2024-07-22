"""
Unit tests for AWS Lambda function using moto to mock S3 interactions.

This module contains helper functions and test cases for the Lambda function.
"""

# Imports
import os
import importlib

import moto
import boto3
import pytest
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
from app.lib.utils import generate_lambda_context, upload_file_to_s3

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


# Test cases
@pytest.mark.parametrize(
    "setup_aws_environment, manifest_filename",
    [
        ("aws_org_1.json", "multiple_rules_valid.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_ous.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_ous.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_accounts.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_accounts.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_some_permission_sets.yaml"),
        ("aws_org_1.json", "multiple_rules_invalid_all_permission_sets.yaml"),
    ],
    indirect=["setup_aws_environment"],
)
def test_access_manifest_reader(setup_aws_environment: pytest.fixture, manifest_filename: str) -> None:
    """
    Test the lambda_handler function with a mocked S3 environment.

    Parameters:
    ----------
    setup_aws_environment : pytest.fixture
        The pytest fixture to set up the AWS environment.

    manifest_filename : str
        The filename of the manifest to be tested.
    """
    with moto.mock_s3():
        # Load manifest file
        manifest_definition_filepath = os.path.join(
            CWD,
            "..",
            "configs",
            "manifests",
            "valid_schema",
            manifest_filename,
        )

        # Arrange
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        upload_file_to_s3(s3_client, BUCKET_NAME, manifest_definition_filepath)

        s3_file_location = f"s3://{BUCKET_NAME}/{manifest_filename}"
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setenv("MANIFEST_FILE_S3_LOCATION", s3_file_location)

        from src.app import index  # pylint: disable=C0415

        importlib.reload(index)

        # Act
        lambda_response = index.lambda_handler(EventBridgeEvent(data={}), context=generate_lambda_context())

        # Assert
        print(lambda_response.body)
