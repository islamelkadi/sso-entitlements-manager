class NoPermissionSetsFoundError(Exception):
    """Raised when no permission sets are available for assignment."""


class NoSSOPrincipalsFoundError(Exception):
    """Raised when no SSO groups or users are found for access assignment."""
