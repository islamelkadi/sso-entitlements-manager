import logging
import functools
from typing import Callable, Any

import boto3
from src.core.constants import SSO_ENTITLMENTS_APP_NAME

def handle_aws_organizations_exceptions(func: Callable) -> Callable:
    """
    Decorator to handle AWS Organizations API exceptions.
    
    Parameters:
    -----------
    func: Callable
        The function to wrap
        
    Returns:
    --------
    Callable
        The wrapped function
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        try:
            return func(self, *args, **kwargs)
        except self._organizations_client.exceptions.ParentNotFoundException as e:
            self._logger.error(f"Invalid parent OU name: {e}")
            raise e
        except self._organizations_client.exceptions.AccessDeniedException as e:
            self._logger.error(f"Missing required IAM policy permissions: {e}")
            raise e
        except Exception as e:
            self._logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise e
    return wrapper

class OrganizationsMapper:

    def __init__(self) -> None:
        """
        Initializes the OrganizationsMapper instance with the root OU ID and optional exclusion lists.

        Parameters:
        ----------
        root_ou_id: str
            The root OU ID.
        exclude_ou_name_list: list, optional
            A list of OU names to exclude. Defaults to an empty list.
        exclude_account_name_list: list, optional
            A list of account names to exclude. Defaults to an empty list.

        Usage:
        ------
        aws_orgs = OrganizationsMapper("root-ou-id", ["ExcludeOU1"], ["ExcludeAccount1"])
        """
        self._logger = logging.getLogger(SSO_ENTITLMENTS_APP_NAME)
        self.exclude_ou_name_list: list = []
        self.exclude_account_name_list: list = []
        self.account_name_id_map: dict = {}
        self.ou_accounts_map: dict = {}
        self._ou_name_id_map: dict = {}
        self._organizations_client: boto3.client = boto3.client("organizations")
        self.root_ou_id: str = self._organizations_client.list_roots()["Roots"][0]["Id"]

    @handle_aws_organizations_exceptions
    def _map_aws_organizational_units(self, parent_ou_id: str = "") -> None:
        """
        Maps AWS organizational units starting from the given parent OU ID.
        """
        aws_ous_flattened_list = []
        parent_ou_id = parent_ou_id if parent_ou_id else self.root_ou_id
        ou_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")
        aws_ou_iterator = ou_paginator.paginate(ParentId=parent_ou_id)

        for page in aws_ou_iterator:
            aws_ous_flattened_list.extend(page["OrganizationalUnits"])

        for ou in aws_ous_flattened_list:
            if ou["Name"] not in self.exclude_ou_name_list and ou["Name"] not in self._ou_name_id_map:
                self._logger.info(f"Traversing non-excluded parent AWS OU: {ou['Name']}")
                self._map_aws_organizational_units(ou["Id"])
                self._ou_name_id_map[ou["Name"]] = ou["Id"]
        self._ou_name_id_map["root"] = self.root_ou_id

    @handle_aws_organizations_exceptions
    def _map_aws_ou_to_accounts(self) -> None:
        """
        Maps AWS accounts to their respective organizational units.
        """
        accounts_paginator = self._organizations_client.get_paginator("list_accounts_for_parent")

        for ou_name, ou_id in self._ou_name_id_map.items():
            self.ou_accounts_map[ou_name] = []
            accounts_iterator = accounts_paginator.paginate(ParentId=ou_id)
            aws_accounts_flattened_list = []

            for page in accounts_iterator:
                aws_accounts_flattened_list.extend(page["Accounts"])

            self._logger.info(f"{ou_name} OU contains {len(aws_accounts_flattened_list)} accounts, creating {ou_name}'s account itenerary...")
            for account in aws_accounts_flattened_list:
                if account["Status"] == "ACTIVE" and account["Name"] not in self.exclude_account_name_list:
                    self._logger.info(f"Appending non-excluded AWS account to {ou_name}'s itenerary")
                    self.ou_accounts_map[ou_name].append({"Id": account["Id"], "Name": account["Name"]})

    def _map_aws_accounts(self) -> None:
        """
        Maps AWS account names to their corresponding IDs
        based on the `ou_accounts_map`.
        """
        for aws_accounts in self.ou_accounts_map.values():
            for account in aws_accounts:
                self.account_name_id_map[account["Name"]] = account["Id"]

    def run_ous_accounts_mapper(self) -> None:
        """
        Runs all mapping methods to update OUs and accounts.
        """
        self._logger.info("Creating AWS OU names to ID map")
        self._map_aws_organizational_units(self.root_ou_id)

        self._logger.info("Creating AWS OU names to account details map")
        self._map_aws_ou_to_accounts()

        self._logger.info("Create AWS account name to ID map")
        self._map_aws_accounts()
