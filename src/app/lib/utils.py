"""
Module consisting of utils functions that are used across
various python modules in this repository.
"""
import os
import json
import logging
import dataclasses
from urllib.parse import urlparse

import yaml
import boto3


LOGGER = logging.getLogger(__name__)


def dict_reverse_lookup(original_dict: dict, lookup_value: str):
    """
    Reverses a flat string to string dictionary and performs
    a look up on the target key.

    Parameters:
    ----------
    original_dict: dict
        The dictionary to reverse.
    lookup_value: str
        Dictionary value to look up.

    Returns:
    -------
    str:
        Dictionary look up value.
    """
    for key, val in original_dict.items():
        if val == lookup_value:
            return key
    return None


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
        A dictionary where the keys are the values of the specified attribute
        from each dictionary in the input list, and the values are the original
        dictionaries.
    """
    result_dict = {}
    for obj in obj_list:
        result_dict[obj[key_attr]] = obj
    return result_dict


def convert_specific_keys_to_uppercase(item: dict = None, keys_to_uppercase: list = None) -> dict:
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
    item = {} if not item else item
    keys_to_uppercase = [] if not keys_to_uppercase else keys_to_uppercase

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
        with open(filepath, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    elif filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        raise ValueError("Unsupported file format. Only .yaml, .yml, and .json are supported.")


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
        invoked_function_arn: str = f"arn:aws:lambda:us-east-1:123456789101:function:{function_name}"
        memory_limit_in_mb: int = 256
        aws_request_id: str = "43723370-e382-466b-848e-5400507a5e86"
        log_group_name: str = f"/aws/lambda/{function_name}"
        log_stream_name: str = "my-log-stream"

        def get_remaining_time_in_millis(self) -> int:
            """Returns mock remaining time in milliseconds for Lambda."""
            return 5

    return LambdaContext()


def download_file_from_s3(s3_object_uri: str, download_path: str = "/tmp") -> None:
    """
    Downloads a file from an S3 bucket to the specified local path.

    Parameters:
    ----------
    bucket_name (str):
        The name of the S3 bucket.

    object_key (str):
        The key of the object to download.

    download_path (str):
        The local file path to download the file to.
    """
    s3_client = boto3.client("s3")

    parsed_s3_uri = urlparse(s3_object_uri)
    s3_bucket_name = parsed_s3_uri.netloc
    s3_object_key = parsed_s3_uri.path.lstrip("/")

    base_filename = os.path.basename(s3_object_key)
    local_destination_filepath = os.path.join(download_path, base_filename)
    s3_client.download_file(s3_bucket_name, s3_object_key, local_destination_filepath)
    return local_destination_filepath


def upload_file_to_s3(bucket_name: str, filepath: str) -> str:
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
    s3_client = boto3.client("s3")

    with open(filepath, "rb") as f:
        object_key = os.path.basename(filepath)
        s3_client.upload_fileobj(f, bucket_name, object_key)
    return object_key
