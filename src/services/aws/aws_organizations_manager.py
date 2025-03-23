import logging
from typing import TypeAlias

import boto3
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.services.aws.utils import handle_aws_exceptions

# Type hints
OuAccountsObject: TypeAlias = list[dict[str, str]]


class AwsOrganizationsManager:
    def __init__(self, root_ou_id: str) -> None:
        self._ou_accounts_map = {}
        self._account_name_id_map: dict[str, str] = {}
        self._logger: logging.Logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)

        # Initialize AWS clients
        self._root_ou_id = root_ou_id
        self._organizations_client = boto3.client("organizations")
        self._accounts_pagniator = self._organizations_client.get_paginator("list_accounts_for_parent")
        self._ous_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")

        self._logger.info("Mapping AWS organization")
        self._generate_aws_organization_map(self._root_ou_id)

    @handle_aws_exceptions()
    def _generate_aws_organization_map(self, ou_id: str) -> None:
        # Get ou name
        if ou_id != self._root_ou_id:
            ou_details = self._organizations_client.describe_organizational_unit(OrganizationalUnitId=ou_id)
            ou_name = ou_details["OrganizationalUnit"]["Name"]
        else:
            ou_name = "root"

        # Add ou entry to ou_accounts map
        if ou_name not in self._ou_accounts_map:
            self._ou_accounts_map[ou_name] = []

        # Get accounts under OU
        for page in self._accounts_pagniator.paginate(ParentId=ou_id):
            for account in page.get("Accounts", []):
                if account["Status"] == "ACTIVE":
                    self._ou_accounts_map[ou_name].append({"Id": account["Id"], "Name": account["Name"]})
                
                if account["Name"] not in self._account_name_id_map:
                    self._account_name_id_map[account["Name"]] = account["Id"]

        # Recursively populate ou account map
        for page in self._ous_paginator.paginate(ParentId=ou_id):
            for child_ou in page.get("OrganizationalUnits", []):
                self._generate_aws_organization_map(child_ou["Id"])

    @property
    def ou_accounts_map(self) -> dict[str, OuAccountsObject]:
        return self._ou_accounts_map

    @property
    def accounts_name_id_map(self) -> dict[str, str]:
        return self._account_name_id_map
