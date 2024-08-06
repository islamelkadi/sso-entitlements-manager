from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from io import StringIO

list_1 = [
    {
        "TargetId": "699753451792",
        "TargetType": "AWS_ACCOUNT",
        "PrincipalId": "2dda9adb-ad02-4dc0-9780-98554bf492e0",
        "PrincipalType": "GROUP",
        "PermissionSetArn": "arn:aws:sso:::instance/ssoins-instanceId/ps-372a284f47cb1c9b",
        "InstanceArn": "arn:aws:sso:::instance/ssoins-instanceId"
    },
    {
        "TargetId": "396981939577",
        "TargetType": "AWS_ACCOUNT",
        "PrincipalId": "2dda9adb-ad02-4dc0-9780-98554bf492e0",
        "PrincipalType": "GROUP",
        "PermissionSetArn": "arn:aws:sso:::instance/ssoins-instanceId/ps-372a284f47cb1c9b",
        "InstanceArn": "arn:aws:sso:::instance/ssoins-instanceId"
    },
    {
        "TargetId": "339186098681",
        "TargetType": "AWS_ACCOUNT",
        "PrincipalId": "2dda9adb-ad02-4dc0-9780-98554bf492e0",
        "PrincipalType": "GROUP",
        "PermissionSetArn": "arn:aws:sso:::instance/ssoins-instanceId/ps-372a284f47cb1c9b",
        "InstanceArn": "arn:aws:sso:::instance/ssoins-instanceId"
    },
    {
        "TargetId": "118964698018",
        "TargetType": "AWS_ACCOUNT",
        "PrincipalId": "2dda9adb-ad02-4dc0-9780-98554bf492e0",
        "PrincipalType": "GROUP",
        "PermissionSetArn": "arn:aws:sso:::instance/ssoins-instanceId/ps-372a284f47cb1c9b",
        "InstanceArn": "arn:aws:sso:::instance/ssoins-instanceId"
    }
]

list_2 = [
    {
        "principal_name": "group1",
        "permission_set_name": "Administrator",
        "target_type": "AWS_ACCOUNT",
        "principal_type": "GROUP",
        "account_name": "workload_1_dev"
    },
    {
        "principal_name": "group1",
        "permission_set_name": "Administrator",
        "target_type": "AWS_ACCOUNT",
        "principal_type": "GROUP",
        "account_name": "workload_2_dev"
    },
    {
        "principal_name": "group1",
        "permission_set_name": "Administrator",
        "target_type": "AWS_ACCOUNT",
        "principal_type": "GROUP",
        "account_name": "workload_1_test"
    },
    {
        "principal_name": "group1",
        "permission_set_name": "Administrator",
        "target_type": "AWS_ACCOUNT",
        "principal_type": "GROUP",
        "account_name": "workload_2_test"
    }
]

def map_target_id_to_account_name(target_id, list_2):
    for item in list_2:
        if item['account_name'] in target_id:
            return item['account_name'], item['principal_name']
    return None, None

def add_comments_and_convert_to_yaml(list_1, list_2):
    yaml = YAML()
    yaml.preserve_quotes = True
    processed_list = []

    for item in list_1:
        account_name, principal_name = map_target_id_to_account_name(item['TargetId'], list_2)
        if account_name and principal_name:
            commented_item = CommentedMap(item)
            commented_item.yaml_add_eol_comment(principal_name, 'PrincipalId')
            commented_item.yaml_add_eol_comment(account_name, 'TargetId')
            processed_list.append(commented_item)
        else:
            processed_list.append(item)

    # Convert to YAML using a StringIO object
    stream = StringIO()
    yaml.dump(processed_list, stream)
    return stream.getvalue()

def save_yaml_to_file(yaml_content, file_name):
    with open(file_name, 'w') as file:
        file.write(yaml_content)
    print(f"YAML content saved to {file_name}")

# Generate YAML content with comments
yaml_content = add_comments_and_convert_to_yaml(list_1, list_2)

# Save to a file
save_yaml_to_file(yaml_content, 'output.yaml')
