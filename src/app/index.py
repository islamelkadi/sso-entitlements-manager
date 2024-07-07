"""
Regex based rules engine for processing regex input for the
purpose of assiging permission sets.
"""
import os
import itertools
from http import HTTPStatus

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler import Response, content_types
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent, event_source


# Env vars
LOG_LEVEL = os.getenv("LOG_LEVEL")
TRACER_SERVICE_NAME = os.getenv("TRACER_SERVICE_NAME")

# AWS Lambda powertool objects & class instances
TRACER = Tracer(service=TRACER_SERVICE_NAME)
LOGGER = Logger(service=TRACER_SERVICE_NAME, level=LOG_LEVEL)


# Lambda Routes
def put_rbac_sso_assignments():
    """
    Lambda function route to create RBAC permission set
    Assignments.
    """

    # Get active AWS accounts
    aws_organizational_map = py_aws_organizations.describe_aws_organizational_unit()
    active_aws_accounts = list(itertools.chain(*aws_organizational_map.values()))

    # Get SSO groups & permission sets
    aws_sso_groups = py_aws_identitycenter.list_sso_groups()
    permission_sets = py_aws_identitycenter.list_permission_sets()

    # Get SSO assignment rules
    sso_assignment_rules = py_ddb.batch_query_items(
        key="RULES", range_begins_with="RULE_"
    )

    # Create SSO assignment
    py_aws_rbac_resolver.create_assignments_mapping(
        aws_accounts=active_aws_accounts,
        sso_groups=aws_sso_groups,
        permission_sets=permission_sets,
        assignment_rules=sso_assignment_rules,
    )

    # return {
    #     "active_aws_accounts": active_aws_accounts,
    #     "sso_groups": sso_groups,
    #     "permission_sets": permission_sets,
    #     "assignment_rules": assifgnment_rules,
    # }


# Lambda handler
@TRACER.capture_lambda_handler
@event_source(data_class=EventBridgeEvent)  # pylint: disable=E1120
@LOGGER.inject_lambda_context(
    log_event=True, correlation_id_path=correlation_paths.EVENT_BRIDGE
)
def lambda_handler(event: EventBridgeEvent, context: LambdaContext):
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
    # return
    return Response(
        status_code=HTTPStatus.OK.value,
        content_type=content_types.APPLICATION_JSON,
        body=put_rbac_sso_assignments(),
    )
