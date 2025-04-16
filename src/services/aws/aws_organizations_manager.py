"""
AWS Organizations Mapping Module

This module provides tools for comprehensive mapping and analysis of AWS Organization structures.
It enables automated discovery and documentation of organizational hierarchies, including
accounts, OUs, and their relationships.

The module defines the following main components:
    - AwsOrganizationsManager: Main class for AWS Organizations mapping
    - OuAccountsObject: Type alias for account list structures

Key Features:
    - Recursive traversal of AWS Organization hierarchy
    - Retrieval of active accounts per organizational unit
    - Creation of name-to-ID mapping for accounts
    - Automatic filtering of inactive accounts
    - Pagination handling for large organizations
    - Comprehensive error handling

Example:
    # Initialize the manager with a root OU ID
    org_manager = AwsOrganizationsManager('ou-root-123abc')

    # Access the full OU to accounts mapping
    ou_accounts = org_manager.ou_accounts_map

    # Get a mapping of account names to their AWS account IDs
    account_ids = org_manager.accounts_name_id_map

Note:
    Requires appropriate AWS IAM permissions to list and describe
    organizational units and accounts, including:
    - organizations:ListAccountsForParent
    - organizations:ListOrganizationalUnitsForParent
    - organizations:DescribeOrganizationalUnit
"""

import logging
from typing import TypeAlias, Literal
from dataclasses import dataclass, field

import boto3
from mypy_boto3_organizations.client import OrganizationsClient
from src.core.custom_classes import SubscriptableDataclass
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.services.aws.utils import handle_aws_exceptions

# Data Classes
@dataclass(kw_only=True, frozen=True)
class AwsAccount(SubscriptableDataclass):
    """Represents an AWS Account"""

    # pylint: disable=invalid-name
    # Class attributes are defined in camel case as AWS API requires
    # them in that format.
    Id: str
    Name: str
    Status: Literal["ACTIVE"] = field(default="ACTIVE")


# Type hints
OuAccountsObject: TypeAlias = list[AwsAccount]

class AwsOrganizationsManager:
    """
    Manages and maps the structure of an AWS Organization.

    This class provides a comprehensive mapping of AWS organizational units
    and their associated accounts, allowing for easy traversal and retrieval
    of organizational structure details.

    Attributes:
        _ou_accounts_map (dict): A nested mapping of organizational unit names to their accounts.
        _account_name_id_map (dict): A mapping of account names to their unique AWS account IDs.
        _logger (logging.Logger): Logger for tracking organization mapping process.

    Properties:
        ou_accounts_map (dict[str, OuAccountsObject]):
            A dictionary where keys are Organizational Unit names and values are
            lists of active accounts. Each account is represented as a dictionary
            with 'Id' and 'Name' keys.

            Example:
                {
                    'root': [
                        {'Id': '123456789012', 'Name': 'Production Account'},
                        {'Id': '210987654321', 'Name': 'Development Account'}
                    ],
                    'Infrastructure': [
                        {'Id': '345678901234', 'Name': 'Network Account'}
                    ]
                }

        accounts_name_id_map (dict[str, str]):
            A dictionary mapping account names to their unique AWS account IDs.

            Example:
                {
                    'Production Account': '123456789012',
                    'Development Account': '210987654321',
                    'Network Account': '345678901234'
                }
    """

    def __init__(self, root_ou_id: str) -> None:
        """
        Initialize the AWS Organizations manager and generate the organization map.

        Args:
            root_ou_id (str): The root Organizational Unit (OU) ID to start mapping from.

        Note:
            This method automatically initiates the organization mapping process
            during instantiation.
        """
        self._ou_accounts_map: dict[str, AwsAccount] = {}
        self._account_name_id_map: dict[str, str] = {}
        self._logger: logging.Logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)

        # Initialize AWS clients
        self._root_ou_id = root_ou_id
        self._organizations_client: OrganizationsClient = boto3.client("organizations")
        self._accounts_pagniator = self._organizations_client.get_paginator(
            "list_accounts_for_parent"
        )
        self._ous_paginator = self._organizations_client.get_paginator(
            "list_organizational_units_for_parent"
        )

        self._logger.info("Mapping AWS organization")
        self._generate_aws_organization_map(self._root_ou_id)

    @handle_aws_exceptions()
    def _generate_aws_organization_map(self, ou_id: str) -> None:
        """
        Recursively generate a comprehensive map of the AWS organization structure.

        This method traverses the organizational hierarchy, collecting information
        about organizational units and their associated accounts.

        Args:
            ou_id (str): The Organizational Unit ID to map.

        Note:
            - Populates _ou_accounts_map with active accounts for each OU
            - Populates _account_name_id_map with unique account identifiers
            - Recursively processes child organizational units
        """
        # Get ou name
        if ou_id != self._root_ou_id:
            ou_details = self._organizations_client.describe_organizational_unit(
                OrganizationalUnitId=ou_id
            )
            ou_name = ou_details["OrganizationalUnit"]["Name"]
        else:
            ou_name = "root"

        # Add ou entry to ou_accounts map
        self._ou_accounts_map[ou_name] = []

        # Get accounts under OU
        for page in self._accounts_pagniator.paginate(ParentId=ou_id):
            for account in page.get("Accounts", []):
                if account["Status"] == "ACTIVE":
                    account = AwsAccount(Id=account["Id"], Name=account["Name"])
                    self._ou_accounts_map[ou_name].append(account)
                self._account_name_id_map[account["Name"]] = account["Id"]

        # Recursively populate ou account map
        for page in self._ous_paginator.paginate(ParentId=ou_id):
            for child_ou in page.get("OrganizationalUnits", []):
                self._generate_aws_organization_map(child_ou["Id"])

    @property
    def ou_accounts_map(self) -> dict[str, OuAccountsObject]:
        """
        Retrieves the mapping of Organizational Units to their accounts.

        Returns:
            dict[str, OuAccountsObject]: A dictionary where keys are OU names
            and values are lists of account dictionaries.
        """
        return self._ou_accounts_map

    @property
    def accounts_name_id_map(self) -> dict[str, str]:
        """
        Retrieves the mapping of account names to their AWS account IDs.

        Returns:
            dict[str, str]: A dictionary mapping account names to their unique IDs.
        """
        return self._account_name_id_map
