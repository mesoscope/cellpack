from .meta_enum import MetaEnum
from cellpack.autopack.AWSHandler import AWSHandler
from cellpack.autopack.FirebaseHandler import FirebaseHandler


class DATABASE_IDS(MetaEnum):
    FIREBASE = "firebase"
    GITHUB = "github"
    AWS = "aws"

    @classmethod
    def with_colon(cls):
        return [f"{ele}:" for ele in cls.values()]

    @classmethod
    def handlers(cls):
        def create_aws_handler(bucket_name, sub_folder_name, region_name):
            return AWSHandler(
                bucket_name=bucket_name,
                sub_folder_name=sub_folder_name,
                region_name=region_name,
            )

        handlers_dict = {
            cls.FIREBASE: FirebaseHandler(),
            cls.AWS: create_aws_handler,
        }
        return handlers_dict
