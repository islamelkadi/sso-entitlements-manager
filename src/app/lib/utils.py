"""
Module consisting of utils functions that are used across
various python modules in this repository.
"""

import json
import yaml
import decimal
import logging
import datetime
import functools
import dataclasses

LOGGER = logging.getLogger(__name__)


def convert_list_to_dict(obj_list: list, key_attr: str) -> dict:
    """
    Converts a list of dictionaries into a dictionary based on a specified attribute.

    Parameters:
    ----------
    obj_list: list
        The list of dictionaries to convert.
    key_attr: str
        The key in each dictionary to use as the key for the resulting dictionary.

    Returns:
    -------
    dict:
        A dictionary where the keys are the values of the specified attribute from each dictionary in the input list,
        and the values are the original dictionaries.
    """
    result_dict = {}
    for obj in obj_list:
        result_dict[obj[key_attr]] = obj
    return result_dict


def convert_specific_keys_to_uppercase(item: dict, keys_to_uppercase: list = []) -> dict:
    """
    Recursively traverse a dictionary and convert the values of specific keys to uppercase.

    Parameters:
    ----------
    item: dict
        Dictionary to be processed.
    keys_to_uppercase: list, optional
        List of keys whose values should be converted to uppercase.

    Returns:
    -------
    dict:
        Dictionary with specified string values converted to uppercase.
    """
    def process_dict(data: dict) -> dict:
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                processed_data[key] = process_dict(value)
            elif isinstance(value, list):
                processed_data[key] = []
                for item in value:
                    if isinstance(item, dict):
                        processed_data[key].append(process_dict(item))
                    else:
                        processed_data[key].append(value.upper() if key in keys_to_uppercase and isinstance(item, str) else item)
            else:
                processed_data[key] = value.upper() if (key in keys_to_uppercase and isinstance(value, str)) else value
        return processed_data
    
    return process_dict(item)


def load_file(filepath: str) -> dict:
    """
    Loads a YAML or JSON file and returns its content as a dictionary.

    Parameters:
    ----------
    filepath: str
        The path to the file to load.

    Returns:
    -------
    dict:
        The content of the file as a dictionary.
    
    Raises:
    ------
    ValueError:
        If the file format is not supported (only .yaml, .yml, and .json are supported).
    """
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


def recursive_process_dict(dict_object: dict) -> dict:
    """
    Recursively parse and process dictionary values and adjust item source datatypes into target datatypes.

    Parameters:
    ----------
    dict_object: dict
        Dictionary object to be processed.

    Returns:
    -------
    dict:
        Processed dictionary object.
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
    Decorator function that handles AWS SSO errors and logs specific exceptions.

    Parameters:
    ----------
    func: function
        The function to decorate.

    Returns:
    -------
    function:
        Safely executed function.
    """
    @functools.wraps(func)
    def execute_function_safely(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_messages = {
                "ConflictException": "Permission set already exists",
                "AccessDeniedException": "Insufficient permissions to perform task",
                "InternalServerException": "Internal server error, check application logs",
                "ResourceNotFoundException": "Specified resource doesn't exist",
                "ThrottlingException": "Invalid input parameters",
                "ValidationException": "Syntax error"
            }
            error_name = type(e).__name__
            LOGGER.error(f"Error occurred: {error_name} - {str(e)}")
            return error_messages.get(error_name, "An error occurred"), 400

    return execute_function_safely


def generate_lambda_context() -> dataclasses.dataclass:
    """
    Creates an AWS Lambda context object instance.

    Returns:
    -------
    LambdaContext:
        Dataclass object representing AWS Lambda context.
    """
    @dataclasses.dataclass
    class LambdaContext:
        """
        AWS Lambda context class mock attributes.

        Attributes:
        ----------
        function_name: str
            Default: "test"
        function_version: str
            Default: "$LATEST"
        invoked_function_arn: str
            Default: "arn:aws:lambda:us-east-1:123456789101:function:test"
        memory_limit_in_mb: int
            Default: 256
        aws_request_id: str
            Default: "43723370-e382-466b-848e-5400507a5e86"
        log_group_name: str
            Default: "/aws/lambda/test"
        log_stream_name: str
            Default: "my-log-stream"
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
            """Returns mock remaining time in milliseconds for Lambda."""
            return 5

    return LambdaContext()
