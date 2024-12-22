"""
Utils module for handling various utility functions related to RBAC management.
"""
import os
import dataclasses
from typing import Dict, Set, List, Any

import boto3
import pytest


def get_ignore_accounts(manifest_file, ou_map) -> Set[str]:
    """
    Determine which accounts should be ignored based on the manifest file and organizational unit map.

    Args:
        manifest_file (ManifestFile): The manifest file containing RBAC rules and exclusions.
        ou_map (OuMap): A map of organizational units and their child accounts.

    Returns:
        Set[str]: A set of account names to ignore.
    """
    ignore_accounts = set()
    ignore_accounts.update(manifest_file.excluded_account_names)
    for ou_name in manifest_file.excluded_ou_names:
        if ou_name in ou_map:
            ignore_accounts.update(account["name"] for account in ou_map[ou_name]["children"] if account["type"] == "ACCOUNT")
    return ignore_accounts


def remove_ignored_targets(manifest_file, ou_map, valid_accounts, sso_users_map, sso_groups_map, sso_permission_sets):
    """
    Remove targets specified in ignore rules from the provided mappings.

    Args:
        manifest_file (ManifestFile): The manifest file containing RBAC rules and exclusions.
        ou_map (OuMap): A map of organizational units and their child accounts.
        valid_accounts (Dict[str, str]): A dictionary mapping valid account names to their IDs.
        sso_users_map (Dict[str, str]): A dictionary mapping SSO user names to their IDs.
        sso_groups_map (Dict[str, str]): A dictionary mapping SSO group names to their IDs.
        sso_permission_sets (Dict[str, str]): A dictionary mapping permission set names to their ARNs.
    """
    ignore_rules = manifest_file.get("ignore", [])
    for rule in ignore_rules:
        for target_name in rule.get("target_names", []):
            if rule["target_type"] == "USER":
                sso_users_map.pop(target_name, None)

            if rule["target_type"] == "GROUP":
                sso_groups_map.pop(target_name, None)

            if rule["target_type"] == "PERMISSION_SET":
                sso_permission_sets.pop(target_name, None)

            if rule["target_type"] == "ACCOUNT":
                valid_accounts.pop(target_name, None)

            if rule["target_type"] == "OU":
                for account in ou_map.get(target_name, []):
                    valid_accounts.pop(account["Name"], None)


def generate_valid_targets(rule, target_names, valid_accounts, ou_map) -> List[str]:
    """
    Generate a list of valid targets based on the rule and target names.

    Args:
        rule (Dict[str, Any]): The RBAC rule.
        target_names (List[str]): The list of target names from the rule.
        valid_accounts (Dict[str, str]): A dictionary mapping valid account names to their IDs.
        ou_map (OuMap): A map of organizational units and their child accounts.

    Returns:
        List[str]: A list of valid target IDs.
    """
    valid_targets = []
    if rule["target_type"] == "ACCOUNT":
        for account_name in target_names:
            if account_name in valid_accounts:
                valid_targets.append(valid_accounts[account_name])
    elif rule["target_type"] == "OU":
        for ou_name in target_names:
            for account in ou_map.get(ou_name, []):
                if account["Name"] in valid_accounts:
                    valid_targets.append(valid_accounts[account["Name"]])
    return valid_targets


def generate_expected_account_assignments(
    manifest_file,
    ou_map,
    identity_store_arn: str,
    valid_accounts: Dict[str, str],
    sso_users_map: Dict[str, str],
    sso_groups_map: Dict[str, str],
    sso_permission_sets: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Generate the expected account assignments based on the manifest file and provided mappings.

    Args:
        manifest_file (ManifestFile): The manifest file containing RBAC rules.
        ou_map (OuMap): A map of organizational units and their child accounts.
        valid_accounts (Dict[str, str]): A dictionary mapping valid account names to their IDs.
        sso_users_map (Dict[str, str]): A dictionary mapping SSO user names to their IDs.
        sso_groups_map (Dict[str, str]): A dictionary mapping SSO group names to their IDs.
        sso_permission_sets (Dict[str, str]): A dictionary mapping permission set names to their ARNs.

    Returns:
        List[Dict[str, Any]]: A list of expected account assignment dictionaries.
    """
    remove_ignored_targets(manifest_file, ou_map, valid_accounts, sso_users_map, sso_groups_map, sso_permission_sets)

    expected_assignments = []
    rbac_rules = manifest_file.get("rbac_rules", [])
    for rule in rbac_rules:
        if rule["principal_type"] == "USER" and rule["principal_name"] not in sso_users_map:
            continue

        if rule["principal_type"] == "GROUP" and rule["principal_name"] not in sso_groups_map:
            continue

        if rule["permission_set_name"] not in sso_permission_sets:
            continue

        target_names = rule.get("target_names", [])
        valid_targets = generate_valid_targets(rule, target_names, valid_accounts, ou_map)

        for target in valid_targets:
            target_assignment_item = {
                "PrincipalId": sso_users_map[rule["principal_name"]] if rule["principal_type"] == "USER" else sso_groups_map[rule["principal_name"]],
                "PrincipalType": rule["principal_type"],
                "PermissionSetArn": sso_permission_sets[rule["permission_set_name"]],
                "TargetId": target,
                "TargetType": "AWS_ACCOUNT",
                "InstanceArn": identity_store_arn,
            }

            if target_assignment_item not in expected_assignments:
                expected_assignments.append(target_assignment_item)

    return expected_assignments


def setup_s3_environment(manifest_definition_filepath: str, bucket_name: str = "my-test-bucket") -> boto3.client:
    """
    Sets up the S3 environment for testing.

    Parameters:
    ----------
    manifest_definition_filepath : str
        The file path to the manifest definition.

    Returns:
    -------
    boto3.client
        The boto3 S3 client.
    """
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket=bucket_name)
    upload_file_to_s3(bucket_name, manifest_definition_filepath)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("MANIFEST_FILE_S3_LOCATION", f"s3://{bucket_name}/{os.path.basename(manifest_definition_filepath)}")

    return s3_client


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
