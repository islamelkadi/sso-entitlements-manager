import os
import glob
import itertools
from typing import Any, Dict, List

import boto3
import pytest
from tests.utils import upload_file_to_s3

# Constants
BUCKET_NAME = "XXXXXXXXXXXXXX"

CWD = os.path.dirname(os.path.realpath(__file__))
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(CWD, "..", "..", "src", "app", "schemas", "manifest_schema_definition.json")

AWS_ORG_DEFINITIONS_FILES_PATH = os.path.join(CWD, "..", "configs", "organizations", "*.json")
AWS_ORG_DEFINITION_FILES = [x for x in glob.glob(AWS_ORG_DEFINITIONS_FILES_PATH)]

VALID_MANIFEST_DEFINITION_FILES_PATH = os.path.join(CWD, "manifests", "*.yaml")
VALID_MANIFEST_DEFINITION_FILES = [x for x in glob.glob(VALID_MANIFEST_DEFINITION_FILES_PATH)]


@pytest.mark.parametrize(
    "setup_live_aws_environment, manifest_filename",
    list(itertools.product(AWS_ORG_DEFINITION_FILES, VALID_MANIFEST_DEFINITION_FILES)),
    indirect=["setup_live_aws_environment"],
)
def test(setup_live_aws_environment: Dict[str, Any], manifest_filename: str):
    sts_client = boto3.client("sts")
    account_number = sts_client.get_caller_identity()["Account"]

    pass
