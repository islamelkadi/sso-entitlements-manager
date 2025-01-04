"""
Module consisting of utils functions that are used across
various python modules in this repository.
"""
import json
import logging
import yaml


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
