"""
Module: test_utils.py

Unit tests for utility functions in lib.utils module.

Tests:
- test_convert_list_to_dict_basic_conversion:
    Test basic conversion of list of dictionaries to dictionary with specified key as index.
- test_convert_list_to_dict_empty_list:
    Test conversion of empty list to empty dictionary.
- test_convert_list_to_dict_duplicate_keys:
    Test handling of duplicate keys during conversion.
- test_convert_list_to_dict_missing_key_attr:
    Test error handling when key attribute is missing in list of dictionaries.
- test_convert_specific_keys_to_uppercase_single_flat_key:
    Test conversion of specific keys to uppercase in a flat dictionary.
- test_convert_specific_keys_to_uppercase_nested_keys:
    Test conversion of specific keys to uppercase in nested dictionaries.
- test_convert_specific_keys_to_uppercase_no_keys_to_uppercase:
    Test conversion when no keys are specified to be converted to uppercase.
- test_convert_specific_keys_to_uppercase_mixed_data_types:
    Test conversion of specific keys to uppercase in a dictionary with mixed data types.
- test_load_yaml_file:
    Test loading YAML file using mock_open and patch decorators.
- test_load_json_file:
    Test loading JSON file using mock_open and patch decorators.
- test_load_unsupported_format:
    Test error handling when loading unsupported file format.
"""
import json
import datetime
from unittest.mock import mock_open, patch
import yaml
import pytest
from src.core.utils import (
    convert_list_to_dict,
    convert_specific_keys_to_uppercase,
    load_file,
)


YAML_CONTENT = """
key1: value1
key2:
  - item1
  - item2
"""

JSON_CONTENT = """
{
  "key1": "value1",
  "key2": ["item1", "item2"]
}
"""


def test_convert_list_to_dict_basic_conversion() -> None:
    """
    Test basic conversion of list of dictionaries to dictionary with specified key as index.
    """
    # Arrange
    obj_list = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"},
    ]
    key_attr = "id"

    # Act
    result = convert_list_to_dict(obj_list, key_attr)

    # Assert
    assert len(result) == len(obj_list)
    assert result[1] == obj_list[0]
    assert result[2] == obj_list[1]
    assert result[3] == obj_list[2]


def test_convert_list_to_dict_empty_list() -> None:
    """
    Test conversion of empty list to empty dictionary.
    """
    # Arrange
    obj_list = []
    key_attr = "id"

    # Act
    result = convert_list_to_dict(obj_list, key_attr)

    # Assert
    assert not result


def test_convert_list_to_dict_duplicate_keys() -> None:
    """
    Test handling of duplicate keys during conversion.
    """
    # Arrange
    obj_list = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 1, "name": "Charlie"},
    ]
    key_attr = "id"

    # Act
    result = convert_list_to_dict(obj_list, key_attr)

    # Assert
    assert result[1]["name"] == "Charlie"
    assert result[2]["name"] == "Bob"
    assert len(result) == 2


def test_convert_list_to_dict_missing_key_attr() -> None:
    """
    Test error handling when key attribute is missing in list of dictionaries.
    """
    # Arrange
    obj_list = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    key_attr = "age"

    # Assert
    with pytest.raises(KeyError):
        # Act
        convert_list_to_dict(obj_list, key_attr)


def test_convert_specific_keys_to_uppercase_single_flat_key() -> None:
    """
    Test conversion of specific keys to uppercase in a flat dictionary.
    """
    # Arrange
    item = {
        "name": "John Doe",
        "age": 30,
        "address": {"city": "New York", "country": "USA"},
        "emails": ["john.doe@example.com", "johndoe@gmail.com"],
    }
    keys_to_uppercase = ["name"]

    expected_result = {
        "name": "JOHN DOE",
        "age": 30,
        "address": {"city": "New York", "country": "USA"},
        "emails": ["john.doe@example.com", "johndoe@gmail.com"],
    }

    # Act
    result = convert_specific_keys_to_uppercase(item, keys_to_uppercase)

    # Assert
    assert result == expected_result


def test_convert_specific_keys_to_uppercase_nested_keys() -> None:
    """
    Test conversion of specific keys to uppercase in nested dictionaries.
    """
    # Arrange
    item = {
        "name": "Alice Smith",
        "age": 25,
        "contacts": {"email": "alice.smith@example.com", "phone": "123-456-7890"},
        "projects": [
            {"title": "Project A", "description": "A project"},
            {"title": "Project B", "description": "Another project"},
        ],
    }
    keys_to_uppercase = ["name", "email", "title"]

    expected_result = {
        "name": "ALICE SMITH",
        "age": 25,
        "contacts": {"email": "ALICE.SMITH@EXAMPLE.COM", "phone": "123-456-7890"},
        "projects": [
            {"title": "PROJECT A", "description": "A project"},
            {"title": "PROJECT B", "description": "Another project"},
        ],
    }

    # Act
    result = convert_specific_keys_to_uppercase(item, keys_to_uppercase)

    # Assert
    assert result == expected_result


def test_convert_specific_keys_to_uppercase_no_keys_to_uppercase() -> None:
    """
    Test conversion when no keys are specified to be converted to uppercase.
    """
    # Arrange
    item = {
        "name": "Jane Doe",
        "age": 35,
        "address": {"city": "San Francisco", "country": "USA"},
    }
    keys_to_uppercase = []

    expected_result = {
        "name": "Jane Doe",
        "age": 35,
        "address": {"city": "San Francisco", "country": "USA"},
    }

    # Act
    result = convert_specific_keys_to_uppercase(item, keys_to_uppercase)

    # Assert
    assert result == expected_result


def test_convert_specific_keys_to_uppercase_mixed_data_types() -> None:
    """
    Test conversion of specific keys to uppercase in a dictionary with mixed data types.
    """
    # Arrange
    item = {
        "name": "Mark",
        "age": 40,
        "details": {"location": "London", "active": True},
        "timestamp": datetime.datetime(
            2024, 7, 7, 10, 30, 0, tzinfo=datetime.timezone.utc
        ),
    }
    keys_to_uppercase = ["name", "location"]

    expected_result = {
        "name": "MARK",
        "age": 40,
        "details": {"location": "LONDON", "active": True},
        "timestamp": datetime.datetime(
            2024, 7, 7, 10, 30, 0, tzinfo=datetime.timezone.utc
        ),
    }

    # Act
    result = convert_specific_keys_to_uppercase(item, keys_to_uppercase)

    # Assert
    assert result == expected_result


@patch("builtins.open", new_callable=mock_open, read_data=YAML_CONTENT)
def test_load_yaml_file(mock_file_open) -> None:
    """
    Test loading YAML file using mock_open and patch decorators.
    """
    # Arrange
    filepath = "test.yaml"

    # Act
    result = load_file(filepath)

    # Assert
    mock_file_open.assert_called_once_with(filepath, "r", encoding="utf-8")
    assert result == yaml.safe_load(YAML_CONTENT)


@patch("builtins.open", new_callable=mock_open, read_data=JSON_CONTENT)
def test_load_json_file(mock_file_open) -> None:
    """
    Test loading JSON file using mock_open and patch decorators.
    """
    # Arrange
    filepath = "test.json"

    # Act
    result = load_file(filepath)

    # Assert
    mock_file_open.assert_called_once_with(filepath, "r", encoding="utf-8")
    assert result == json.loads(JSON_CONTENT)


def test_load_unsupported_format() -> None:
    """
    Test error handling when loading unsupported file format.
    """
    # Assert
    with pytest.raises(ValueError, match="Unsupported file format"):
        # Act
        load_file("test.txt")
