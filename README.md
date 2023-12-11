# aws-cloud-pass
[![Linting](https://github.com/islamelkadi/sso-manager/actions/workflows/linting.yaml/badge.svg)](https://github.com/islamelkadi/sso-manager/actions/workflows/linting.yaml)

[![Testing](https://github.com/islamelkadi/sso-manager/actions/workflows/testing.yaml/badge.svg)](https://github.com/islamelkadi/sso-manager/actions/workflows/testing.yaml)

[![Scanning](https://github.com/islamelkadi/sso-manager/actions/workflows/scanning.yaml/badge.svg)](https://github.com/islamelkadi/sso-manager/actions/workflows/scanning.yaml)

## Explicit assignment use cases
- Single Account ID
- Multiple Account IDs

- Root OU ID
- Single OU ID
- Multiple OU IDs

- OU IDs without inheritence
- OU IDs with inheritence
- OU IDs with limitied inheritence


### Case 1 - SSO Group to Account ID

Input <sso-group-name>:<account-id>

1. Validate <sso-group-name> is actually a group that exists
2. If <sso-group> doesn't exists:
    - throw an error
3. Else:
    - fetch <sso-group> guid

