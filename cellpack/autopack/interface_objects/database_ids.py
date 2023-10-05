from .meta_enum import MetaEnum
from cellpack.autopack.FirebaseHandler import FirebaseHandler


class DATABASE_IDS(MetaEnum):
    FIREBASE = "firebase"
    GITHUB = "github"

    @classmethod
    def with_colon(cls):
        return [f"{ele}:" for ele in cls.values()]

    @classmethod
    def handlers(cls):
        return {cls.FIREBASE: FirebaseHandler()}
