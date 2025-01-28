import logging
from typing import Union, TypeAlias
from functools import cached_property

import boto3
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.services.aws.utils import handle_aws_exceptions

# Type hints
OuAccountsObject: TypeAlias = list[dict[str, str]]

class OrganizationsMapper:

    def __init__(self) -> None:
    
        self.ou_accounts_map = {}
        self._logger: logging.Logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)

        # Initialize AWS clients
        self._organizations_client = boto3.client("organizations")
        self.root_ou_id = self._organizations_client.list_roots()["Roots"][0]["Id"]
        self._ous_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")
        self._accounts_pagniator = self._organizations_client.get_paginator("list_accounts_for_parent")

        self._logger.info("Mapping AWS organization")
        self._generate_aws_organization_map(self.root_ou_id)


    @handle_aws_exceptions()
    def _generate_aws_organization_map(self, ou_id: str) -> None:

        # Get ou name
        if ou_id != self.root_ou_id:
            ou_details = self._organizations_client.describe_organizational_unit(OrganizationalUnitId=ou_id)
            ou_name = ou_details["OrganizationalUnit"]["Name"]
        else:
            ou_name = "root"

        # Add ou entry to ou_accounts map
        if ou_name not in self.ou_accounts_map:
            self.ou_accounts_map[ou_name] = {"Id": ou_id, "Accounts": []}

        # Get accounts under OU
        for page in self._accounts_pagniator.paginate(ParentId=ou_id):
            for account in page.get("Accounts", []):
                if account["Status"] == "ACTIVE":
                    self.ou_accounts_map[ou_name]["Accounts"].append({"Id": account["Id"], "Name": account["Name"]})

        # Recursively populate ou account map
        for page in self._ous_paginator.paginate(ParentId=ou_id):
            for child_ou in page.get("OrganizationalUnits", []):
                self._generate_aws_organization_map(child_ou["Id"])


    @cached_property
    def ou_accounts_map(self) -> dict[str, dict[str, Union[str, OuAccountsObject]]]:
        return self.ou_accounts_map


    @cached_property
    def account_name_id_map(self) -> dict[str, str]:
        account_name_id_map: dict[str, str] = {}
        for ou_details in self.ou_accounts_map.values():
            for account_details in ou_details:
                account_name_id_map[account_details["Name"]] = account_details["Id"]
        return account_name_id_map


    @cached_property
    def ou_name_id_map(self) -> dict[str, str]:
        ou_name_id_map: dict[str, str] = {}
        for ou_name, ou_details in self.ou_accounts_map.items():
                ou_name_id_map[ou_name] = ou_details["Id"]
        return ou_name_id_map
