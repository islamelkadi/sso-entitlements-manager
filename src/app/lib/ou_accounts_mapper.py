"""
Module to interact with the AWS Organizations service.
"""
import itertools
import boto3
from .utils import convert_list_to_dict


class AwsOrganizations:
    """
    Class to manage interactions with the AWS Organizations service.

    Attributes:
    ----------
    ou_account_map: dict
        A dictionary mapping OU names to lists of accounts.
    _ou_name_id_map: dict
        A dictionary mapping OU names to their IDs.
    _root_ou_id: str
        The root OU ID.
    _exclude_ou_name_list: list
        A list of OU names to exclude.
    _exclude_account_name_list: list
        A list of account names to exclude.
    _organizations_client: boto3.client
        The Boto3 client for AWS Organizations.
    _account_parent_paginator: boto3.Paginator
        Paginator for listing account parents.
    _account_paginator: boto3.Paginator
        Paginator for listing accounts for a parent OU.
    _ou_paginator: boto3.Paginator
        Paginator for listing organizational units for a parent OU.
    account_map: dict
        A dictionary mapping account names to account details.

    Methods:
    --------
    __init__(root_ou_id: str, exclude_ou_name_list: list = [], exclude_account_name_list: list = []) -> None:
        Initializes the AwsOrganizations instance.
    _map_aws_organizational_units(parent_ou_id: str = "") -> None:
        Maps AWS organizational units starting from the given parent OU ID.
    _map_aws_ou_to_accounts() -> None:
        Maps AWS accounts to their respective organizational units.
    """

    def __init__(
        self,
        root_ou_id: str,
        exclude_ou_name_list: list = [],
        exclude_account_name_list: list = [],
    ) -> None:
        """
        Initializes the AwsOrganizations instance.

        Parameters:
        ----------
        root_ou_id: str
            The root OU ID.
        exclude_ou_name_list: list, optional
            A list of OU names to exclude. Default is an empty list.
        exclude_account_name_list: list, optional
            A list of account names to exclude. Default is an empty list.

        Usage:
        ------
        aws_orgs = AwsOrganizations("root-ou-id", ["ExcludeOU1"], ["ExcludeAccount1"])
        """
        self.ou_account_map = {}
        self._ou_name_id_map = {}
        self._root_ou_id = root_ou_id
        self._exclude_ou_name_list = exclude_ou_name_list
        self._exclude_account_name_list = exclude_account_name_list

        self._organizations_client = boto3.client("organizations")

        self._account_parent_paginator = self._organizations_client.get_paginator(
            "list_parents"
        )
        self._account_paginator = self._organizations_client.get_paginator(
            "list_accounts_for_parent"
        )
        self._ou_paginator = self._organizations_client.get_paginator(
            "list_organizational_units_for_parent"
        )

        self._map_aws_organizational_units(self._root_ou_id)
        self._map_aws_ou_to_accounts()
        self.account_map = convert_list_to_dict(
            list(itertools.chain.from_iterable(self.ou_account_map.values())), "Name"
        )

    def _map_aws_organizational_units(self, parent_ou_id: str = "") -> None:
        """
        Maps AWS organizational units starting from the given parent OU ID.

        Parameters:
        ----------
        parent_ou_id: str, optional
            The parent OU ID to start mapping from. Defaults to the root OU ID.

        Usage:
        ------
        self._map_aws_organizational_units()
        self._map_aws_organizational_units("parent-ou-id")
        """
        parent_ou_id = parent_ou_id if parent_ou_id else self._root_ou_id
        aws_ous_flattened_list = []
        aws_ou_iterator = self._ou_paginator.paginate(ParentId=parent_ou_id)
        for page in aws_ou_iterator:
            aws_ous_flattened_list.extend(page["OrganizationalUnits"])

        for ou in aws_ous_flattened_list:
            if (
                ou["Name"] not in self._exclude_ou_name_list
                and ou["Name"] not in self._ou_name_id_map
            ):
                self._map_aws_organizational_units(ou["Id"])
                self._ou_name_id_map[ou["Name"]] = ou["Id"]
        self._ou_name_id_map["root"] = self._root_ou_id

    def _map_aws_ou_to_accounts(self) -> None:
        """
        Maps AWS accounts to their respective organizational units.

        Usage:
        ------
        self._map_aws_ou_to_accounts()
        """
        for ou_name, ou_id in self._ou_name_id_map.items():
            self.ou_account_map[ou_name] = []
            accounts_iterator = self._account_paginator.paginate(ParentId=ou_id)
            aws_accounts_flattened_list = []
            for page in accounts_iterator:
                aws_accounts_flattened_list.extend(page["Accounts"])

            for account in aws_accounts_flattened_list:
                if (
                    account["Status"] == "ACTIVE"
                    and account["Name"] not in self._exclude_account_name_list
                ):
                    self.ou_account_map[ou_name].append(
                        {"Id": account["Id"], "Name": account["Name"]}
                    )
