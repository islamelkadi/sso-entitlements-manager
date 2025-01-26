import logging
from typing import Union, Set
from functools import cached_property

import boto3
from src.core.constants import SSO_ENTITLMENTS_APP_NAME
from src.services.aws.utils import handle_aws_exceptions

class OrganizationsMapper:

    def __init__(self, exclude_ou_names: Union(Set(str), None) = set(), exclude_account_names = Set(str)) -> None:
        self._logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
        
        # Initialize private backing fields
        self._ou_name_id_map = {}
        self.ou_accounts_map = {}
        self.account_name_id_map = {}
        self.suspended_aws_accounts = set()

        # Set via properties
        self.invalid_ou_names = set()
        self._excluded_ou_names = exclude_ou_names

        self.invalid_account_names = set()
        self._excluded_account_names = exclude_account_names

        # Initialize AWS clients
        self._organizations_client = boto3.client("organizations")
        self._ous_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")
        self._accounts_pagniator = self._organizations_client.get_paginator("list_accounts_for_parent")
        self.root_ou_id = self._organizations_client.list_roots()["Roots"][0]["Id"]

        self._logger.info("Mapping AWS organization")
        self._map_aws_organization(self.root_ou_id)



    @handle_aws_exceptions()
    def _map_aws_organization(self, ou_id: str) -> None:
        if ou_id != self.root_ou_id:
            ou_response = self._organizations_client.describe_organizational_unit(OrganizationalUnitId=ou_id)
            ou_name = ou_response["OrganizationalUnit"]["Name"]
        else:
            ou_name = "root"

        self.ou_accounts_map[ou_name] = {"id": ou_id, "accounts": []}
        accounts_paginator = self._organizations_client.get_paginator("list_accounts_for_parent")
        for page in accounts_paginator.paginate(ParentId=ou_id):
            for account in page.get("Accounts", []):
                if account["Status"] == "ACTIVE":
                    self.ou_accounts_map[ou_name]["accounts"].append({"Id": account["Id"], "Name": account["Name"]})
                else:
                    self.suspended_aws_accounts.add(account["Name"])
                    self._logger.info(f"AWS Account {account['Name']} in SUSPENDED state. Dropping account from OU Accounts map...")

        ou_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")
        for page in ou_paginator.paginate(ParentId=ou_id):
            for child_ou in page.get("OrganizationalUnits", []):
                self._map_aws_organization(child_ou["Id"])


