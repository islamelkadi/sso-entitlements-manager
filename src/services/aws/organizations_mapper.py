import logging
from typing import Optional, List, Set

import boto3
from src.core.utils import handle_aws_exceptions
from src.core.constants import SSO_ENTITLMENTS_APP_NAME

class OrganizationsMapper:

    def __init__(self) -> None:
        self._logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)

        self.excluded_ou_names: Set[str] = set()
        self.invalid_ou_names: Set[str] = set()

        self.excluded_account_names: Set[str] = set()
        self.invalid_account_names: Set[str] = set()

        self._ou_name_id_map: dict = {}
        self.ou_accounts_map: dict = {}
        self.account_name_id_map: dict = {}

        self._organizations_client: boto3.client = boto3.client("organizations")
        self.root_ou_id: str = self._organizations_client.list_roots()["Roots"][0]["Id"]

        self._logger.info("Creating AWS OU names to ID map")
        self._map_aws_organizational_units(self.root_ou_id)

    @handle_aws_exceptions()
    def _map_aws_organizational_units(self, parent_ou_id: str = "") -> None:
        parent_ou_id = parent_ou_id if parent_ou_id else self.root_ou_id
        ou_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")
        aws_ou_iterator = ou_paginator.paginate(ParentId=parent_ou_id)

        for page in aws_ou_iterator:
            for ou in page.get("OrganizationalUnits", []):
                if ou["Name"] not in self.excluded_ou_names and ou["Name"] not in self._ou_name_id_map:
                    self._logger.debug(f"Traversing non-excluded parent AWS OU: {ou['Name']}")
                    self._map_aws_organizational_units(ou["Id"])
                    self._ou_name_id_map[ou["Name"]] = ou["Id"]
        self._ou_name_id_map["root"] = self.root_ou_id

    @handle_aws_exceptions()
    def _map_aws_ou_to_accounts(self) -> None:
        accounts_paginator = self._organizations_client.get_paginator("list_accounts_for_parent")
        for ou_name, ou_id in self._ou_name_id_map.items():
            self.ou_accounts_map[ou_name] = []
            accounts_iterator = accounts_paginator.paginate(ParentId=ou_id)
            for page in accounts_iterator:
                self._logger.info(f"{ou_name} OU contains {len(aws_accounts_flattened_list)} accounts, creating {ou_name}'s account itenerary...")
                for account in page.get("Accounts", []):
                    if account["Status"] == "ACTIVE" and account["Name"] not in self.excluded_account_names:
                        self._logger.debug(f"Appending non-excluded AWS account to {ou_name}'s itenerary")
                        self.ou_accounts_map[ou_name].append({"Id": account["Id"], "Name": account["Name"]})

    def _map_aws_accounts(self) -> None:
        for aws_accounts in self.ou_accounts_map.values():
            for account in aws_accounts:
                self.account_name_id_map[account["Name"]] = account["Id"]

    def run_ous_accounts_mapper(self) -> None:

        self._logger.info("Creating AWS OU names to account details map")
        self._map_aws_ou_to_accounts()

        self._logger.info("Create AWS account name to ID map")
        self._map_aws_accounts()


    @property
    def excluded_ou_names(self) -> Set[str]:
        return self.excluded_ou_names
    
    @excluded_ou_names.setter
    def excluded_ou_names(self, names: List[str]) -> None:
        excluded_ou_names = set(names)
        self._logger.debug(f"Provided AWS OU names to exclude: {', '.join(sorted(self.excluded_ou_names))}")

        self.excluded_ou_names = {x for x in excluded_ou_names if x in self._ou_name_id_map}
        self._logger.debug(f"Valid AWS OU names to exclude: {', '.join(sorted(self.excluded_ou_names))}")

        self.invalid_ou_names = excluded_ou_names - self.excluded_ou_names
        self._logger.debug(f"Invalid provided AWS OU names: {', '.join(sorted(self.invalid_ou_names))}")

    @property
    def excluded_account_names(self) -> Set[str]:
        pass

    @excluded_account_names.setter
    def excluded_account_names(self, names: List[str) -> None:
        # TODO: Filter out invalid account names
        self.excluded_account_names = set(names)
        self._logger.info(f"Set excluded AWS account names: {', '.join(sorted(self.excluded_account_names))}")

