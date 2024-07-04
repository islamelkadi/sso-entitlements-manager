"""
Module to interact with the AWS Organizations service
"""
import itertools
import boto3
from .utils import convert_list_to_dict


class AwsOrganizations:

    def __init__(self, root_ou_id: str, exclude_ou_name_list: list = [], exclude_account_name_list: list = []) -> None:

        # Set instance vars
        self.ou_to_account_map = {}
        self._ou_name_id_map = {}
        self._root_ou_id = root_ou_id
        self._exclude_ou_name_list = exclude_ou_name_list
        self._exclude_account_name_list = exclude_account_name_list

        # Set boto3 clients
        self._organizations_client = boto3.client("organizations")

        # Set paginators
        self._account_parent_paginator = self._organizations_client.get_paginator("list_parents")
        self._account_paginator = self._organizations_client.get_paginator("list_accounts_for_parent")
        self._ou_paginator = self._organizations_client.get_paginator("list_organizational_units_for_parent")

        # Create Account & OU itenerary
        self._map_aws_organizational_units(self._root_ou_id)
        self._map_aws_ou_to_accounts()
        self.account_map = convert_list_to_dict(
            list(itertools.chain.from_iterable(self.ou_to_account_map.values())), "Name"
        )


    def _map_aws_organizational_units(self, parent_ou_id: str = "") -> None:
        parent_ou_id = parent_ou_id if parent_ou_id else self._root_ou_id
        aws_ous_flattened_list = []
        aws_ou_iterator = self._ou_paginator.paginate(ParentId=parent_ou_id)
        for page in aws_ou_iterator:
            aws_ous_flattened_list.extend(page["OrganizationalUnits"])

        for ou in aws_ous_flattened_list:
            if ou["Name"] not in self._exclude_ou_name_list and ou["Name"] not in self._ou_name_id_map:
                self._map_aws_organizational_units(ou["Id"])
                self._ou_name_id_map[ou["Name"]] = ou["Id"]
        self._ou_name_id_map["root"] = self._root_ou_id


    def _map_aws_ou_to_accounts(self):
        for ou_name, ou_id in self._ou_name_id_map.items():
            self.ou_to_account_map[ou_name] = []
            accounts_iterator = self._account_paginator.paginate(ParentId=ou_id)
            aws_accounts_flattened_list = []
            for page in accounts_iterator:
                aws_accounts_flattened_list.extend(page["Accounts"])

            for account in aws_accounts_flattened_list:
                if account["Status"] == "ACTIVE" and account["Name"] not in self._exclude_account_name_list:
                    self.ou_to_account_map[ou_name].append({"Id": account["Id"], "Name": account["Name"]})
