import logging
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlunparse

import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class AWSHandler(object):
    """
    Handles all the AWS S3 operations
    """

    # class attributes
    _session_created = False
    _s3_client = None

    def __init__(
        self,
        bucket_name,
        sub_folder_name=None,
        region_name=None,
    ):
        self.bucket_name = bucket_name
        self.folder_name = sub_folder_name
        self.sub_folder_name = sub_folder_name
        self.region_name = region_name
        # Create a session if one does not exist
        if not AWSHandler._session_created:
            self._create_session(region_name)
            AWSHandler._session_created = True
        else:
            # use the existing session
            self.s3_client = AWSHandler._s3_client

    def _create_session(self, region_name):
        AWSHandler._s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://s3.{region_name}.amazonaws.com",
            region_name=region_name,
        )
        self.s3_client = AWSHandler._s3_client

    def get_aws_object_key(self, object_name):
        if self.folder_name is not None:
            object_name = f"{self.folder_name}/{object_name}"
        else:
            object_name = object_name
        return object_name

    def upload_file(self, file_path, s3_key=None):
        """Upload a file to an S3 bucket
        :param file_path: File to upload
        :param s3_key: Custom S3 object key. If not specified, uses file name with folder prefix
        :return: S3 key if file was uploaded, else False
        """

        if s3_key is None:
            file_name = Path(file_path).name
            object_name = self.get_aws_object_key(file_name)
        else:
            object_name = s3_key

        # Upload the file
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            self.s3_client.put_object_acl(
                ACL="public-read", Bucket=self.bucket_name, Key=object_name
            )

        except ClientError as e:
            logging.error(e)
            return False
        return object_name

    def download_file(self, key, local_file_path):
        """
        Download a file from S3
        :param key: S3 object key
        :param local_file_path: Local file path to save the downloaded file
        """

        try:
            self.s3_client.download_file(self.bucket_name, key, local_file_path)
            print("File downloaded successfully.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print("The object does not exist.")
            else:
                print("An error occurred while downloading the file.")

    def create_presigned_url(self, object_name, expiration=3600):
        """Generate a presigned URL to share an S3 object
        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """
        object_name = self.get_aws_object_key(object_name)
        # Generate a presigned URL for the S3 object
        # The response contains the presigned URL
        # https://{self.bucket_name}.s3.{region}.amazonaws.com/{object_key}
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
            base_url = urlunparse(urlparse(url)._replace(query="", fragment=""))
            return base_url
        except ClientError as e:
            logging.error(f"Error generating presigned URL: {e}")
            return None

    def is_url_valid(self, url):
        """
        Validate the url's scheme, bucket name, and query parameters, etc.
        """
        parsed_url = urlparse(url)
        # Check the scheme
        if parsed_url.scheme != "https":
            return False
        # Check the bucket name
        if not parsed_url.path.startswith(f"/{self.bucket_name}/"):
            return False
        # Check unwanted query parameters
        unwanted_query_params = ["AWSAccessKeyId", "Signature", "Expires"]
        if parsed_url.query:
            query_params = parse_qs(parsed_url.query)
            for param in unwanted_query_params:
                if param in query_params:
                    return False
        return True

    def save_file_and_get_url(self, file_path):
        """
        Uploads a file to S3 and returns the base url
        """
        try:
            s3_key = self.upload_file(file_path)
            if s3_key:
                # extract just the filename for use as document ID (remove any folder paths)
                file_name = Path(s3_key).name
                base_url = self.create_presigned_url(file_name)
                if file_name and base_url:
                    if self.is_url_valid(base_url):
                        return file_name, base_url
        except NoCredentialsError as e:
            logging.debug(f"AWS credentials are not configured: {e}")
            return None, None
        return None, None

    def upload_directory(self, local_directory_path, s3_prefix=""):
        """
        Upload an entire directory to S3, preserving the directory structure
        :param local_directory_path: local path to the directory to upload
        :param s3_prefix: s3 prefix to prepend to all uploaded files
        :return: dictionary with upload results
        """

        local_path = Path(local_directory_path)
        if not local_path.exists() or not local_path.is_dir():
            logging.error(f"Directory does not exist: {local_directory_path}")
            return {"success": False, "uploaded_files": [], "errors": []}

        uploaded_files = []
        errors = []
        total_size = 0

        for root, dirs, files in os.walk(local_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_file_path, local_path)

                # create S3 key with prefix and relative path
                if s3_prefix:
                    s3_key = f"{s3_prefix}/{relative_path.replace(os.sep, '/')}"
                else:
                    s3_key = relative_path.replace(os.sep, "/")

                try:
                    file_size = os.path.getsize(local_file_path)
                    uploaded_s3_key = self.upload_file(local_file_path, s3_key)

                    if uploaded_s3_key:
                        uploaded_files.append(
                            {
                                "local_path": local_file_path,
                                "s3_key": uploaded_s3_key,
                                "size": file_size,
                            }
                        )
                        total_size += file_size

                    else:
                        error_msg = f"upload error - {relative_path}: upload_file returned False"
                        logging.error(error_msg)
                        errors.append(error_msg)
                except Exception as e:
                    error_msg = f"upload error - {relative_path}: {e}"
                    logging.error(error_msg)
                    errors.append(error_msg)

        return {
            "success": len(errors) == 0,
            "uploaded_files": uploaded_files,
            "errors": errors,
            "total_files": len(uploaded_files),
            "total_size": total_size,
        }
