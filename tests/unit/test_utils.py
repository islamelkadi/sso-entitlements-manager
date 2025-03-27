"""
Module: test_utils.py

Comprehensive unit tests for utility functions in lib.utils module.

This test suite validates the functionality of key utility functions including:
- List to dictionary conversion
- Specific key uppercase conversion
- File loading mechanisms

Key Test Scenarios:
------------------
1. List to Dictionary Conversion:
   - Basic conversion
   - Empty list handling
   - Duplicate key management
   - Missing key attribute error handling

2. Uppercase Key Conversion:
   - Flat dictionary conversion
   - Nested dictionary conversion
   - Mixed data type handling
   - No-op scenarios

3. File Loading:
   - YAML file loading
   - JSON file loading
   - Unsupported file format handling

Dependencies:
------------
- pytest: For test assertion and exception testing
- unittest.mock: For mocking file operations
- yaml: For YAML file parsing
- json: For JSON file parsing

Example:
    To run tests:
    $ pytest test_utils.py

Note:
    Requires pytest and appropriate mock libraries for execution.
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


# Test data for file loading tests
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

    Validates that:
    - The resulting dictionary has the correct length
    - Each item is correctly mapped by its key attribute
    - Order and content of items are preserved

    Test Strategy:
    - Create a list of dictionaries with unique identifiers
    - Convert list to dictionary using 'id' as key
    - Assert dictionary size and item mapping
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

    Validates that:
    - An empty input list returns an empty dictionary
    - No errors are raised during conversion

    Test Strategy:
    - Provide an empty list
    - Convert to dictionary
    - Assert resulting dictionary is empty
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
    Test handling of duplicate keys during list to dictionary conversion.

    Validates that:
    - Duplicate keys result in overwriting of previous entries
    - Final dictionary retains only the last encountered entry for a key
    - Resulting dictionary size is reduced to unique keys

    Test Strategy:
    - Create a list with duplicate key values
    - Convert to dictionary
    - Assert last entry for each key is preserved
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

    Validates that:
    - A KeyError is raised when the specified key attribute does not exist
    - Error occurs before any partial conversion takes place

    Test Strategy:
    - Attempt to convert list with non-existent key
    - Assert KeyError is raised
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

    Validates that:
    - Specified keys are converted to uppercase
    - Other keys and nested structures remain unchanged
    - Non-string values are preserved

    Test Strategy:
    - Create a flat dictionary with mixed data types
    - Specify a single key to convert to uppercase
    - Assert only the specified key is converted
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

    Validates that:
    - Keys are converted to uppercase at different nesting levels
    - Conversion works with lists of dictionaries
    - Other data types and structures remain unmodified

    Test Strategy:
    - Create a nested dictionary with multiple levels and list of dictionaries
    - Specify keys to convert in different locations
    - Assert correct uppercase conversion
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

    Validates that:
    - When no keys are specified, the input dictionary remains unchanged
    - No modifications are made to the original dictionary

    Test Strategy:
    - Create a dictionary with various keys
    - Provide an empty list of keys to convert
    - Assert the dictionary remains identical
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

    Validates that:
    - Uppercase conversion works with various data types
    - Non-string values are preserved
    - Datetime objects remain unchanged
    - Nested structures are correctly processed

    Test Strategy:
    - Create a dictionary with mixed data types including datetime
    - Specify keys to convert across different levels
    - Assert correct uppercase conversion while preserving other types
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

    Validates that:
    - YAML file is opened with correct parameters
    - Content is correctly parsed using yaml.safe_load
    - File is read with UTF-8 encoding

    Test Strategy:
    - Mock file opening mechanism
    - Provide predefined YAML content
    - Assert file is opened correctly
    - Verify parsed content matches expectations
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

    Validates that:
    - JSON file is opened with correct parameters
    - Content is correctly parsed using json.loads
    - File is read with UTF-8 encoding

    Test Strategy:
    - Mock file opening mechanism
    - Provide predefined JSON content
    - Assert file is opened correctly
    - Verify parsed content matches expectations
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

    Validates that:
    - Attempting to load an unsupported file format raises a ValueError
    - Error message clearly indicates unsupported format
    - No partial loading or silent failure occurs

    Test Strategy:
    - Attempt to load a file with an unsupported extension
    - Assert ValueError is raised with specific error message
    """
    # Assert
    with pytest.raises(ValueError, match="Unsupported file format"):
        # Act
        load_file("test.txt")
