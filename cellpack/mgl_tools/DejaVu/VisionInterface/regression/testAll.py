import sys
from mglutil.regression import testplus

import test_dejavu

harness = testplus.TestHarness(
    "testAll_DejaVu_ViPEr",
    funs=[],
    dependents=[
        test_dejavu.harness,
    ],
)

if __name__ == "__main__":
    testplus.chdir()
    print harness
    sys.exit(len(harness))
