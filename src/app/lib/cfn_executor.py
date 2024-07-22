# import uuid
# import boto3
# import botocore
# import botocore.exceptions


# class CfnExecutor:
#     def __init__(self) -> None:
#         self._cfn_client = boto3.client("cloudformation")

#     def check_stack_exists(self, stack_name):
#         """
#         Check if a CloudFormation stack exists.

#         Parameters:
#         ----------
#         stack_name (str): The name of the CloudFormation stack.

#         Returns:
#         -------
#         bool: True if the stack exists, False otherwise.
#         """
#         client = boto3.client("cloudformation")

#         try:
#             # Attempt to describe the stack
#             response = client.describe_stacks(StackName=stack_name)
#             # If the stack is found, it exists
#             return True
#         except botocore.exceptions.ClientError as e:
#             # If the error code is 'ValidationError', it means the stack doesn't exist
#             if "ValidationError" in str(e):
#                 return False
#             # Re-raise the exception if it's a different error
#             raise
