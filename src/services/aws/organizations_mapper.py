import logging
from typing import List, Set
from functools import cached_property

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

        self._logger.info("Creating AWS account names to ID map")
        self._map_aws_accounts()

    @handle_aws_exceptions()
    def _map_aws_organizational_units(self) -> None:
        pass

    @handle_aws_exceptions()
    def _map_aws_organization(self) -> None:
        accounts_paginator = self._organizations_client.get_paginator("list_accounts")
        for page in accounts_paginator.paginate():
            for account in page.get("Accounts", []):
                if account["Status"] == "ACTIVE":
                    account_arn = account["Arn"]
                    ou_id = # regex pattern to find OU ID
                    if ou_id not in self.ou_accounts_map:
                        self.ou_accounts_map[ou_id] = set()
                    


    def run_ous_accounts_mapper(self) -> None:

        self._logger.info("Creating AWS OU names to account details map")
        self._map_aws_ou_to_accounts()


    @cached_property
    def filtered_ou_map(self) -> Set[str]:
        return self.excluded_ou_names
    
    @excluded_ou_names.setter
    def excluded_ou_names(self, names: List[str]) -> None:
        excluded_ou_names = set(names)
        self._logger.debug(f"Provided AWS OU names to exclude: {', '.join(sorted(self.excluded_ou_names))}")

        self.excluded_ou_names = {x for x in excluded_ou_names if x in self._ou_name_id_map}
        self._logger.debug(f"Valid AWS OU names to exclude: {', '.join(sorted(self.excluded_ou_names))}")

        self.invalid_ou_names = excluded_ou_names - self.excluded_ou_names
        self._logger.debug(f"Invalid provided AWS OU names: {', '.join(sorted(self.invalid_ou_names))}")

    
    # @cached_property
    # def excluded_account_names(self) -> Set[str]:
    #     return self.excluded_account_names

    @excluded_account_names.setter
    def excluded_account_names(self, names: List[str]) -> None:
        excluded_account_names = set(names)
        self._logger.debug(f"Provided AWS account names to exclude: {', '.join(sorted(self.excluded_account_names))}")

        self.excluded_account_names = {x for x in excluded_account_names if x in self.account_name_id_map}
        self._logger.debug(f"Valid AWS OU names to exclude: {', '.join(sorted(self.excluded_account_names))}")

        self.invalid_account_names = excluded_account_names - self.excluded_account_names
        self._logger.debug(f"Invalid provided AWS account names: {', '.join(sorted(self.invalid_account_names))}")
