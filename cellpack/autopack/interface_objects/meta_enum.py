from enum import Enum


class MetaEnum(str, Enum):
    @classmethod
    def values(cls):
        return [member.value for member in cls]

    @classmethod
    def is_member(cls, item):
        values = cls.values()
        return item in values
