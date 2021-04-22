#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run autopack from recipe file
"""

# Standard library
import sys
import os
import logging
from typing import Any, Tuple
import traceback

# Third party
# from PIL import Image
import numpy
import argparse

# Relative
import cellpack.mgl_tools.upy as upy
from cellpack import autopack, get_module_version
from cellpack.autopack.Environment import Environment
from cellpack.autopack.Graphics import AutopackViewer as AFViewer
from cellpack.autopack.Analysis import AnalyseAP
###############################################################################

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s"
)

###############################################################################


class Args(argparse.Namespace):

    DEFAULT_TWOD = True
    DEFAULT_ANALYSIS = True
    DEFAULT_RECIPE_FILE = "/test-recipes/NM_Analysis_FigureA1.0.xml"

    def __init__(self):
        # Arguments that could be passed in through the command line
        self.twoD = self.DEFAULT_TWOD
        self.analysis = self.DEFAULT_ANALYSIS
        self.recipe = os.path.join(os.getcwd(), self.DEFAULT_RECIPE_FILE)
        self.debug = False
        #
        self.__parse()

    def __parse(self):
        p = argparse.ArgumentParser(
            prog="run_exmaple",
            description="A simple example of a bin script",
        )

        p.add_argument(
            "-v",
            "--version",
            action="version",
            version="%(prog)s " + get_module_version(),
        )
        p.add_argument(
            "-t",
            "--two-d",
            action="store",
            dest="twoD",
            type=int,
            default=self.twoD,
            help="The dimensions of the packing",
        )
        p.add_argument(
            "-a",
            "--analysis",
            action="store",
            dest="analysis",
            type=int,
            default=self.analysis,
            help="The mode of the packing",
        )
        p.add_argument(
            "--debug",
            action="store_true",
            dest="debug",
            help=argparse.SUPPRESS,
        )
        p.parse_args(namespace=self)


###############################################################################


def main():
    args = Args()
    dbg = args.debug
    try:

        # Do your work here - preferably in a class or function,
        # passing in your args. E.g.
        # exe = Example(args.recipe)
        # exe.update_value(args.second)
        print("Recipe : {}\n".format(args.recipe))
        helperClass = upy.getHelperClass()
        helper = helperClass(vi="nogui")
        autopack.helper = helper
        fileName = os.path.basename(args.recipe)

        evn = Environment(name=fileName)

    except Exception as e:
        log.error("=============================================")
        log.error("\n\n" + traceback.format_exc())
        log.error("=============================================")
        sys.exit(1)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()
