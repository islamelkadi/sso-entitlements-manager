"""
Utility Functions Module

This module provides a collection of helper functions for common data manipulation 
and file handling tasks across the repository. It includes utilities for:
    - Dictionary transformations
    - List conversions
    - File loading
    - Logging setup

The functions are designed to be flexible, reusable, and support various data processing needs.

Key Features:
    - Reverse dictionary lookup
    - List to dictionary conversion
    - Key-based uppercase conversion
    - YAML and JSON file loading
    - Flexible logging configuration
"""

import json
import atexit
import pathlib
import logging
import logging.config
import logging.handlers
import yaml


def dict_reverse_lookup(original_dict: dict, lookup_value: str):
    """
    Performs a reverse lookup in a dictionary to find a key by its value.

    This function searches through a dictionary to find the key corresponding
    to a specific value. It is useful when you need to retrieve a key based on
    its associated value in a flat dictionary.

    Args:
        original_dict (dict): The dictionary to search through.
        lookup_value (str): The value to find the corresponding key for.

    Returns:
        str or None: The key associated with the lookup value, or None if
        no matching key is found.

    Examples:
        >>> data = {'a': '1', 'b': '2', 'c': '3'}
        >>> dict_reverse_lookup(data, '2')
        'b'
        >>> dict_reverse_lookup(data, '4')
        None
    """
    for key, val in original_dict.items():
        if val == lookup_value:
            return key
    return None


def convert_list_to_dict(obj_list: list, key_attr: str) -> dict:
    """
    Transforms a list of dictionaries into a dictionary indexed by a specific key.

    This function converts a list of dictionaries into a dictionary where the
    keys are determined by a specified attribute in each dictionary. This is
    useful for creating lookup tables or reorganizing data structures.

    Args:
        obj_list (list): A list of dictionaries to convert.
        key_attr (str): The key in each dictionary to use as the new dictionary's key.

    Returns:
        dict: A dictionary where keys are values of the specified attribute,
        and values are the original dictionaries.

    Raises:
        KeyError: If the specified key does not exist in one of the dictionaries.

    Examples:
        >>> data = [
        ...     {'id': 1, 'name': 'Alice'},
        ...     {'id': 2, 'name': 'Bob'}
        ... ]
        >>> convert_list_to_dict(data, 'id')
        {1: {'id': 1, 'name': 'Alice'}, 2: {'id': 2, 'name': 'Bob'}}
    """
    result_dict = {}
    for obj in obj_list:
        result_dict[obj[key_attr]] = obj
    return result_dict


def convert_specific_keys_to_uppercase(
    item: dict = None, keys_to_uppercase: list = None
) -> dict:
    """
    Recursively converts specified dictionary keys' values to uppercase.

    This function traverses a nested dictionary and converts values to uppercase
    for specified keys. It supports deep nested structures including dictionaries
    and lists of dictionaries.

    Args:
        item (dict, optional): Dictionary to be processed. Defaults to an empty dict.
        keys_to_uppercase (list, optional): List of keys whose string values
            should be converted to uppercase. Defaults to an empty list.

    Returns:
        dict: A new dictionary with specified string values converted to uppercase.

    Examples:
        >>> data = {
        ...     'user': {'name': 'john', 'email': 'JOHN@example.com'},
        ...     'tags': ['work', 'personal']
        ... }
        >>> convert_specific_keys_to_uppercase(data, keys_to_uppercase=['name'])
        {'user': {'name': 'JOHN', 'email': 'JOHN@example.com'}, 'tags': ['work', 'personal']}
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
                        processed_data[key].append(
                            value.upper()
                            if key in keys_to_uppercase and isinstance(item, str)
                            else item
                        )
            else:
                processed_data[key] = (
                    value.upper()
                    if (key in keys_to_uppercase and isinstance(value, str))
                    else value
                )
        return processed_data

    return process_dict(item)


def load_file(filepath: str) -> dict:
    """
    Loads and parses YAML or JSON files into a dictionary.

    This function supports loading configuration or data files in YAML and JSON
    formats. It provides a convenient way to read file contents with automatic
    format detection.

    Args:
        filepath (str): Path to the file to be loaded.

    Returns:
        dict: The parsed contents of the file.

    Raises:
        ValueError: If the file format is not supported (.yaml, .yml, or .json).

    Examples:
        >>> load_file('config.yaml')
        {'database': {'host': 'localhost', 'port': 5432}}
        >>> load_file('settings.json')
        {'debug': true, 'log_level': 'INFO'}
    """
    if filepath.endswith((".yaml", ".yml")):
        with open(filepath, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    elif filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    else:
        raise ValueError(
            "Unsupported file format. Only .yaml, .yml, and .json are supported."
        )


def setup_logging(
    log_level: str = "INFO",
    logging_config_filepath: str = "logging/configs/config.json",
) -> None:
    """
    Configures the logging system based on a JSON configuration file.

    This function sets up logging with the following key operations:
    - Loads logging configuration from a specified JSON file
    - Creates log directories if they don't exist
    - Configures logging levels and handlers
    - Starts a queue listener for asynchronous logging

    Args:
        log_level (str, optional): Logging level to set. Defaults to "INFO".
        logging_config_filepath (str, optional): Path to the logging configuration
            JSON file. Defaults to "logging/configs/config.json".

    Note:
        - Supports dynamic log level configuration
        - Automatically creates necessary log directories
        - Uses a queue handler for improved logging performance
    """
    # Load logging file
    config_file = pathlib.Path(logging_config_filepath)
    with open(config_file, encoding="UTF-8") as fp:
        config = json.load(fp)

    # Create logs directory if it doesn't exist
    log_file = pathlib.Path(config["handlers"]["file_json"]["filename"])
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Override config file root logging level
    config["loggers"]["root"]["level"] = log_level

    # Configure logging level & log queue handler
    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
