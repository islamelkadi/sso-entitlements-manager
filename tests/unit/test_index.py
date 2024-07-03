# """
# Unit tests to test writing regex rules from DDB
# """

# # Imports
# import importlib
# import pytest
# from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent
# from app.lib.utils import generate_lambda_context


# def test(
#     setup_aws_organization: pytest.fixture,
#     setup_identity_store: pytest.fixture,
#     setup_dynamodb: pytest.fixture
# ) -> None:

#     # Arrange
#     context = generate_lambda_context()
#     monkeypatch = pytest.MonkeyPatch()
#     monkeypatch.setenv("ROOT_OU_ID", setup_aws_organization["root_ou_id"])

#     from src.app import index
#     importlib.reload(index)

#     # Act
#     lambda_response = index.lambda_handler(EventBridgeEvent(data={}), context)
#     print(lambda_response.body)

#     # Assert
