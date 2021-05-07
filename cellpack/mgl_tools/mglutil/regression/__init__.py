import sys
import string

VERSION = sys.version.split()[0]

if VERSION >= "2.1":
    from . import testplus
else:
    from . import testplus_before_2_1

    testplus = testplus_before_2_1
