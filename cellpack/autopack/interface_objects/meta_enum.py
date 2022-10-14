from enum import Enum


class MetaEnum(Enum):
    @classmethod
    def values(cls):
        return [member.value for member in cls]

    @classmethod
    def is_member(cls, item):
        values = cls.values()
        return item in values
