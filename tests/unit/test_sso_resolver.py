import os
import pytest
from app.lib.aws_sso_resolver import AwsResolver

# Globals vars
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

@pytest.mark.order(1)
@pytest.mark.parametrize("setup_aws_environment", ["aws_org_1.json"], indirect=True)
def test_create_rbac_assignments(setup_aws_environment: pytest.fixture) -> None:

    # Arrange
    manifest_definition_filepath = os.path.join(CWD, "..", "configs", "manifests", "missing_rules.yaml")
    aws_sso_resolver = AwsResolver(MANIFEST_SCHEMA_DEFINITION_FILEPATH, manifest_definition_filepath)

    # 