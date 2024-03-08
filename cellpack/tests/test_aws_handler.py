from unittest.mock import patch
from moto import mock_aws
from cellpack.autopack.AWSHandler import AWSHandler
import boto3


# Mocking the session creation
@patch("cellpack.autopack.AWSHandler.boto3.client")
def test_create_session(mock_client):
    with mock_aws():
        aws_handler = AWSHandler(
            bucket_name="test_bucket",
            sub_folder_name="test_folder",
            region_name="us-west-2",
        )
        assert aws_handler.s3_client is not None
        mock_client.assert_called_once_with(
            "s3",
            endpoint_url="https://s3.us-west-2.amazonaws.com",
            region_name="us-west-2",
        )


def test_get_aws_object_key():
    with mock_aws():
        aws_handler = AWSHandler(
            bucket_name="test_bucket",
            sub_folder_name="test_folder",
            region_name="us-west-2",
        )
        object_key = aws_handler.get_aws_object_key("test_file")
        assert object_key == "test_folder/test_file"


def test_upload_file():
    with mock_aws():
        aws_handler = AWSHandler(
            bucket_name="test_bucket",
            sub_folder_name="test_folder",
            region_name="us-west-2",
        )
        s3 = boto3.client("s3", region_name="us-west-2")
        s3.create_bucket(
            Bucket="test_bucket",
            CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
        )
        with open("test_file.txt", "w") as file:
            file.write("test file")
        file_name = aws_handler.upload_file("test_file.txt")
        assert file_name == "test_file.txt"


# def test_create_presigned_url():
#     with mock_aws():
#         aws_handler = AWSHandler(
#             bucket_name="test_bucket",
#             sub_folder_name="test_folder",
#             region_name="us-west-2",
#         )
#         s3 = boto3.client("s3", region_name="us-west-2")
#         s3.create_bucket(
#             Bucket="test_bucket",
#             CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
#         )
#         with open("test_file.txt", "w") as file:
#             file.write("test file")
#         aws_handler.upload_file("test_file.txt")
#         url = aws_handler.create_presigned_url("test_file.txt")
#         assert url is not None
#         assert url.startswith(
#             "https://test_bucket.s3.us-west-2.amazonaws.com/test_folder/test_file.txt"
#         )


# def test_is_url_valid():
#     with mock_aws():
#         aws_handler = AWSHandler(
#             bucket_name="test_bucket",
#             sub_folder_name="test_folder",
#             region_name="us-west-2",
#         )
#         s3 = boto3.client("s3", region_name="us-west-2")
#         s3.create_bucket(
#             Bucket="test_bucket",
#             CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
#         )
#         with open("test_file.txt", "w") as file:
#             file.write("test file")
#         aws_handler.upload_file("test_file.txt")
#         url = aws_handler.create_presigned_url("test_file.txt")
#         print("test--------", url)
#         assert aws_handler.is_url_valid(url) is True
#         assert aws_handler.is_url_valid("invalid_url") is False
#         assert (
#             aws_handler.is_url_valid(
#                 "https://test_bucket.s3.us-west-2.amazonaws.com/test_folder/test_file.txt"
#             )
#             is True
#         )
#         assert (
#             aws_handler.is_url_valid(
#                 "https://test_bucket.s3.us-west-2.amazonaws.com/test_folder/test_file.txt?AWSAccessKeyId=1234"
#             )
#             is False
#         )
