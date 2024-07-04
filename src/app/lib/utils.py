"""
Python module consisting of utils functions that are used accross
the various python modules in this repo
"""

import json
import yaml
import decimal
import logging
import datetime
import functools
import dataclasses


LOGGER = logging.getLogger(__name__)


def convert_list_to_dict(obj_list: list, key_attr: str):
    """
    Converts a list of dictionaries into a dictionary based on a specified attribute.

    Parameters:
    obj_list (list of dict): The list of dictionaries to convert.
    key_attr (str): The key in each dictionary to use as the key for the resulting dictionary.

    Returns:
    dict: A dictionary where the keys are the values of the specified attribute from each dictionary in the input list,
          and the values are the original dictionaries.

    Example:
    >>> obj_list = [
    ...     {'DisplayName': 'user1', 'UserName': 'user1@testing.com'},
    ...     {'DisplayName': 'user2', 'UserName': 'user2@testing.com'}
    ... ]

    >>> list_to_dict(obj_list, 'DisplayName')
    {'user1': {'DisplayName': 'user1', 'UserName': 'user1@testing.com'},
     'user2': {'DisplayName': 'user2', 'UserName': 'user2@testing.com'}}

    """
    return {obj[key_attr]: obj for obj in obj_list}


def convert_specific_keys_to_lowercase(item: dict, keys_to_lowercase: list = []):
    """
    Recursively traverse a dictionary and convert the values of specific keys to lowercase.

    :param item: Dictionary to be processed
    :param keys_to_convert: List of keys whose values should be converted to lowercase
    :return: Dictionary with specified string values converted to lowercase
    """
    def process_dict(data):
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                processed_data[key] = process_dict(value)
            elif isinstance(value, list):
                processed_data[key] = [process_dict(item) if isinstance(item, dict) else (item.lower() if isinstance(item, str) else item) for item in value]
            else:
                processed_data[key] = value.lower() if (key in keys_to_lowercase and isinstance(value, str)) else value
        return processed_data
    
    return process_dict(item)


def load_file(filepath: str) -> dict:
    """Loads a YAML or JSON file and returns its content as a dictionary."""
    if filepath.endswith((".yaml", ".yml")):
        with open(filepath, "r") as file:
            return yaml.safe_load(file)
    elif filepath.endswith(".json"):
        with open(filepath, "r") as file:
            return json.load(file)
    else:
        raise ValueError(
            "Unsupported file format. Only .yaml, .yml, and .json are supported."
        )


def recursive_process_dict(dict_object: dict):
    """
    Utils function to recursively parse and process dictionary values
    and adjust item source datatypes into target dataypes

    Parameters
    ----------
        - dict_object: dict, required
            Dictionary object to be processed

    Returns
    -------
    dict_object:
        Processed dictionary object
    """
    for k, v in dict_object.items():
        if isinstance(v, dict):
            recursive_process_dict(v)
        else:
            if isinstance(v, (int, float)):
                dict_object[k] = decimal.Decimal(v)
            elif isinstance(v, decimal.Decimal):
                dict_object[k] = float(v)
            elif isinstance(v, datetime.datetime):
                dict_object[k] = v.strftime("%y-%m-%d %H:%M:%S")
            else:
                continue
    return dict_object


def handle_aws_sso_errors(func):
    """
    Decorator functions that acts on or return passed function

    Parameters
    ----------
        - func: required
    """

    @functools.wraps(func)
    # pylint: disable=C0116
    # pylint: disable=R1710
    def execute_function_safely(*args, **kwargs):
        # pylint: disable=R0911
        """Function to execute passed in function, or capture exceptions
        and return error message and code based on exception type

        Returns
        -------
        func:
            safely executed function
        """
        # pylint: disable=W0718
        # pylint: disable=R1705
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if type(e).__name__ == "ConflictException":
                LOGGER.error(e)
                return "Permission set already exists", 400
            elif type(e).__name__ == "AccessDeniedException":
                LOGGER.error(e)
                return "Insufficient permissions to perform task", 400
            elif type(e).__name__ == "InternalServerException":
                LOGGER.error(e)
                return "Internal server error, check application logs", 500
            elif type(e).__name__ == "ResourceNotFoundException":
                LOGGER.error(e)
                return "Specified resource doesn't exist", 400
            elif type(e).__name__ == "ThrottlingException":
                LOGGER.error(e)
                return "Invalid input parameters", 400
            elif type(e).__name__ == "ValidationException":
                LOGGER.error(e)
                return "Syntax error", 400

    return execute_function_safely


def generate_lambda_context():
    """
    Utils function to create lambda context object instance

    Returns
    -------
    LambdaContext:
        Dataclass object to AWS Lambda context
    """

    @dataclasses.dataclass
    class LambdaContext:
        """
        Creates an AWS Lambda context class. This class's attributes
        consists of the following mock attributes:

            - function_name: str, default: test
            - function_version: str, default: $LATEST
            - invoked_function_arn: str, default: \
                arn:aws:lambda:us-east-1:123456789101:function:test
            - memory_limit_in_mb: int, default: 256
            - aws_request_id: str, default: 810d00ae-669c-4100-88dd-334888a04cc2
            - log_group_name: str, default: /aws/lambda/test
            - log_stream_name: str, default: my-log-stream
        """

        function_name: str = "test"
        function_version: str = "$LATEST"
        invoked_function_arn: str = (
            f"arn:aws:lambda:us-east-1:123456789101:function:{function_name}"
        )
        memory_limit_in_mb: int = 256
        aws_request_id: str = "43723370-e382-466b-848e-5400507a5e86"
        log_group_name: str = f"/aws/lambda/{function_name}"
        log_stream_name: str = "my-log-stream"

        def get_remaining_time_in_millis(self) -> int:
            """Return mock remaining time in milli seconds for lambda"""
            return 5

    return LambdaContext()
