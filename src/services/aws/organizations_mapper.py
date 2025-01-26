import logging
from typing import Set
from functools import cached_property

import boto3
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.services.aws.utils import handle_aws_exceptions

class OrganizationsMapper:

    def __init__(self, exclude_ou_names = set(), exclude_account_names = set()) -> None:
    
        self.ou_accounts_map = {}
        self._logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
        self._excluded_ou_names = exclude_ou_names if exclude_ou_names else set()
        self._excluded_account_names = exclude_account_names if exclude_account_names else set()

        # Initialize AWS clients
        self._organizations_client = boto3.client("organizations")
        self._ous_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")
        self._accounts_pagniator = self._organizations_client.get_paginator("list_accounts_for_parent")
        self.root_ou_id = self._organizations_client.list_roots()["Roots"][0]["Id"]

        self._logger.info("Mapping AWS organization")
        self._map_aws_organization(self.root_ou_id)


    @handle_aws_exceptions()
    def _map_aws_organization(self, ou_id: str) -> None:

        # Get ou name
        if ou_id != self.root_ou_id:
            ou_details = self._organizations_client.describe_organizational_unit(OrganizationalUnitId=ou_id)
            ou_name = ou_details["OrganizationalUnit"]["Name"]
        else:
            ou_name = "root"

        # Add ou entry to ou_accounts map
        if ou_name not in self.ou_accounts_map:
            self.ou_accounts_map[ou_name] = {"id": ou_id, "accounts": []}

        # Get accounts under OU
        accounts_paginator = self._organizations_client.get_paginator("list_accounts_for_parent")
        for page in accounts_paginator.paginate(ParentId=ou_id):
            for account in page.get("Accounts", []):
                if account["Status"] == "ACTIVE":
                    self.ou_accounts_map[ou_name]["accounts"].append({"id": account["Id"], "name": account["Name"]})

        # Recursively populate ou account map
        ou_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")
        for page in ou_paginator.paginate(ParentId=ou_id):
            for child_ou in page.get("OrganizationalUnits", []):
                self._map_aws_organization(child_ou["Id"])

    @cached_property
    def get_org_map(self):
        ou_name_id_map = {}
        account_name_id_map = {}
        for ou_name, ou_detail in self.ou_accounts_map.items():
            ou_name_id_map[ou_name] = ou_detail["id"]
            for account_details in ou_detail["accounts"]:
                account_name_id_map[account_details["name"]] = account_details["id"]