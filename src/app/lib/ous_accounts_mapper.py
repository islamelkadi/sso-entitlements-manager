"""
Module to interact with the AWS Organizations service.
"""
import boto3


class AwsOrganizations:
    """
    Class to manage interactions with the AWS Organizations service.

    Attributes:
    ----------
    ou_name_accounts_details_map: dict
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
    account_map: dict
        A dictionary mapping account names to account details.

    Methods:
    --------
    __init__(root_ou_id: str, exclude_ou_name_list: list = None,
                exclude_account_name_list: list = []) -> None:
        Initializes the AwsOrganizations instance.
    _map_aws_organizational_units(parent_ou_id: str = "") -> None:
        Maps AWS organizational units starting from the given parent OU ID.
    _map_aws_ou_to_accounts() -> None:
        Maps AWS accounts to their respective organizational units.
    """

    def __init__(
        self,
        root_ou_id: str,
        exclude_ou_name_list: list = None,
        exclude_account_name_list: list = None,
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
        self.account_name_id_map = {}
        self.ou_name_accounts_details_map = {}

        self._ou_name_id_map = {}
        self._root_ou_id = root_ou_id
        self._exclude_ou_name_list = (
            [] if not exclude_ou_name_list else exclude_ou_name_list
        )
        self._exclude_account_name_list = (
            [] if not exclude_account_name_list else exclude_account_name_list
        )

        self._organizations_client = boto3.client("organizations")

        self._map_aws_organizational_units(self._root_ou_id)
        self._map_aws_ou_to_accounts()
        self._map_aws_accounts()

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
        ou_paginator = self._organizations_client.get_paginator(
            "list_organizational_units_for_parent"
        )
        parent_ou_id = parent_ou_id if parent_ou_id else self._root_ou_id
        aws_ous_flattened_list = []
        aws_ou_iterator = ou_paginator.paginate(ParentId=parent_ou_id)
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
        accounts_paginator = self._organizations_client.get_paginator(
            "list_accounts_for_parent"
        )

        for ou_name, ou_id in self._ou_name_id_map.items():
            self.ou_name_accounts_details_map[ou_name] = []
            accounts_iterator = accounts_paginator.paginate(ParentId=ou_id)
            aws_accounts_flattened_list = []
            for page in accounts_iterator:
                aws_accounts_flattened_list.extend(page["Accounts"])

            for account in aws_accounts_flattened_list:
                if (
                    account["Status"] == "ACTIVE"
                    and account["Name"] not in self._exclude_account_name_list
                ):
                    self.ou_name_accounts_details_map[ou_name].append(
                        {"Id": account["Id"], "Name": account["Name"]}
                    )

    def _map_aws_accounts(self) -> None:
        """
        Maps AWS account names to their corresponding IDs
        based on the `ou_name_accounts_details_map`.
        """
        aws_accounts = []
        for account_set in self.ou_name_accounts_details_map.values():
            aws_accounts.extend(account_set)

        for account in aws_accounts:
            self.account_name_id_map[account["Name"]] = account["Id"]
