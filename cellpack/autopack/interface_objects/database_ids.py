from .meta_enum import MetaEnum


class DATABASE_IDS(MetaEnum):
    FIREBASE = "firebase"
    GITHUB = "github"

    @classmethod
    def with_colon(cls):
        return [f"{ele}:" for ele in cls.values()]
