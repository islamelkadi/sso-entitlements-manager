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
from app.lib.utils import generate_lambda_context

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


# Helper functions
def upload_file_to_s3(s3_client, bucket_name: str, filepath: str) -> str:
    """
    Upload a file to an S3 bucket.

    Parameters
    ----------
    s3_client : boto3.client
        The boto3 S3 client.

    bucket_name : str
        The name of the S3 bucket.

    filepath : str
        The local file path to upload.

    Returns
    -------
    str
        The object key of the uploaded file.
    """
    with open(filepath, "rb") as f:
        object_key = os.path.basename(filepath)
        s3_client.upload_fileobj(f, bucket_name, object_key)
    return object_key


# Test cases
@pytest.mark.parametrize(
    "setup_aws_environment, manifest_filename",
    [
        ("aws_org_1.json", "multiple_rules_valid.yaml"),
    ],
    indirect=["setup_aws_environment"],
)
def test_lambda_handler(
    setup_aws_environment: pytest.fixture,  # pylint: disable=W0613
    manifest_filename: str,
) -> None:
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
