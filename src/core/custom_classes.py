from dataclasses import asdict


class SubscriptableDataclass:
    """
    A base class that makes dataclasses subscriptable and convertible to dictionaries.

    Provides dictionary-like access to dataclass fields and conversion to dictionary format.
    """

    def __getitem__(self, key: str) -> str:
        """
        Enables dictionary-style access to dataclass fields.

        Args:
            key (str): The field name to access

        Returns:
            str: The value of the requested field
        """
        return asdict(self)[key]

    def to_dict(self) -> dict[str, str]:
        """
        Converts the dataclass instance to a dictionary.

        Returns:
            dict[str, str]: Dictionary representation of the dataclass
        """
        return asdict(self)
