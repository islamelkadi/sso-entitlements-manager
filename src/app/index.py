"""
Regex based rules engine for processing regex input for the
purpose of assiging permission sets.
"""
import os
from http import HTTPStatus

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent, event_source

from app.lib.access_control_resolver import AwsAccessResolver

# Globals
CWD = os.path.dirname(os.path.realpath(__file__))
MANIFEST_SCHEMA_DEFINITION_FILEPATH = os.path.join(
    CWD,
    "schemas",
    "manifest_schema_definition.json",
)

# Env vars
LOG_LEVEL = os.getenv("LOG_LEVEL")
TRACER_SERVICE_NAME = os.getenv("TRACER_SERVICE_NAME")
MANIFEST_FILE_S3_LOCATION = os.getenv("MANIFEST_FILE_S3_LOCATION")

# AWS Lambda powertool objects & class instances
TRACER = Tracer(service=TRACER_SERVICE_NAME)
LOGGER = Logger(service=TRACER_SERVICE_NAME, level=LOG_LEVEL)

# Class instance
ACCESS_RESOLVER = AwsAccessResolver(
    MANIFEST_FILE_S3_LOCATION, MANIFEST_SCHEMA_DEFINITION_FILEPATH
)


# Lambda handler
@TRACER.capture_lambda_handler
@event_source(data_class=EventBridgeEvent)  # pylint: disable=E1120
@LOGGER.inject_lambda_context(
    log_event=True, correlation_id_path=correlation_paths.EVENT_BRIDGE
)
def lambda_handler(
    event: EventBridgeEvent, context: LambdaContext
):  # pylint: disable=W0613
    """
    Function to create or retrieve regex rules for SSO permission
    set assignments

    Parameters
    ----------
    event: dict, required
        Input event to the Lambda function

    context: object, required
        Lambda Context runtime methods and attributes

    Returns
    ------
    response: dict
        - body: contains stringified response of lambda function
        - statusCode: contains HTTP status code
    """
    return Response(
        status_code=HTTPStatus.OK.value,
        content_type=content_types.APPLICATION_JSON,
        body={
            "successful_account_assignments": ACCESS_RESOLVER.successful_rbac_assignments,
            "failed_account_assignments": ACCESS_RESOLVER.failed_rbac_assignments,
        },
    )
