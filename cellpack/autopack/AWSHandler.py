import logging
import boto3
from botocore.exceptions import ClientError
from pathlib import Path


class AWSHandler(object):
    """
    Handles all the AWS S3 operations
    """

    def __init__(
        self,
        bucket_name,
        sub_folder_name=None,
        region_name=None,
    ):
        self.bucket_name = bucket_name
        self.folder_name = sub_folder_name
        session = boto3.Session()
        self.s3_client = session.client(
            "s3",
            endpoint_url=f"https://s3.{region_name}.amazonaws.com",
            region_name=region_name,
        )

    def get_aws_object_key(self, object_name):
        if self.folder_name is not None:
            object_name = self.folder_name + object_name
        else:
            object_name = object_name
        return object_name

    def upload_file(self, file_path):
        """Upload a file to an S3 bucket
        :param file_path: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_path is used
        :return: True if file was uploaded, else False
        """

        file_name = Path(file_path).name

        object_name = self.get_aws_object_key(file_name)
        # Upload the file
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            self.s3_client.put_object_acl(
                ACL="public-read", Bucket=self.bucket_name, Key=object_name
            )

        except ClientError as e:
            logging.error(e)
            return False
        return file_name

    def create_presigned_url(self, object_name, expiration=3600):
        """Generate a presigned URL to share an S3 object
        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """
        object_name = self.get_aws_object_key(object_name)
        # Generate a presigned URL for the S3 object
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            logging.error(e)
            return None
        # The response contains the presigned URL
        # https://{self.bucket_name}.s3.{region}.amazonaws.com/{object_key}
        return url