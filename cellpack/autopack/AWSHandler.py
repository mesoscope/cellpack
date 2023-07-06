import logging
import boto3
from botocore.exceptions import ClientError
import os

class AWSHandler(object):
    """
    Handles all the AWS S3 operations
    """

    def __init__(self, bucket_name, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key, # TODO: check how do we want to handle credentials?
            region_name=region_name
        )


    def upload_file(self, file_name, folder_name=None, object_name=None):
        """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :return: True if file was uploaded, else False
        """

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = folder_name + os.path.basename(file_name)
        else:
            object_name = folder_name + object_name

        # Upload the file
        try:
            response = self.s3_client.upload_file(file_name, self.bucket_name, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True