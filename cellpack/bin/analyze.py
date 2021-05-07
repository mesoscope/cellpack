#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run autopack from recipe file
"""

# Standard library
import sys
import os
import logging
import traceback

# Third party
import numpy
import argparse

# Relative
import cellpack.mgl_tools.upy as upy
from cellpack import autopack, get_module_version
from cellpack.autopack.Environment import Environment
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
    DEFAULT_RECIPE_FILE = "cellpack/test-recipes/NM_Analysis_FigureA1.0.xml"
    DEFAULT_OUTPUT_FILE = "/Users/meganriel-mehan/Dropbox/cellPack/NM_Analysis_A2_2/"

    def __init__(self):
        # Arguments that could be passed in through the command line
        self.twoD = self.DEFAULT_TWOD
        self.analysis = self.DEFAULT_ANALYSIS
        self.recipe = os.path.join(os.getcwd(), self.DEFAULT_RECIPE_FILE)
        self.output = self.DEFAULT_OUTPUT_FILE
        self.debug = True
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
            "-r",
            "--recipe",
            action="store",
            dest="recpie",
            type=str,
            default=self.recipe,
            help="Relative path to the recipe file for packing",
        )
        p.add_argument(
            "-o",
            "--output",
            action="store",
            dest="output",
            type=str,
            default=self.output,
            help="Full path for where to store the results file",
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
            type=bool,
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
        recipePath = args.recipe
        doAnalysis = args.analysis
        output = args.output
        twoD = args.twoD
        print("Recipe : {}\n".format(args.recipe))
        localdir = wrkDir = autopack.__path__[0]
        helperClass = upy.getHelperClass()

        helper = helperClass(vi="nogui")
        autopack.helper = helper
        fileName = os.path.basename(recipePath)

        env = Environment(name=fileName)
        env.helper = helper
        env.loadRecipe(recipePath)
        afviewer = None

        env.saveResult = False

        def setCompartment(ingr):
            ingr.rejectionThreshold = 60  # [1,1,0]#
            ingr.nbJitter = 6

        env.loopThroughIngr(setCompartment)

        if doAnalysis:
            env.placeMethod = "RAPID"
            env.encapsulatingGrid = 0
            autopack.testPeriodicity = False
            analyse = AnalyseAP(env=env, viewer=afviewer, result_file=None)
            analyse.g.Resolution = 1.0
            env.boundingBox = numpy.array(env.boundingBox)
            analyse.doloop(10, env.boundingBox, wrkDir, output, rdf=True, render=False, twod=twoD, use_file=True)  # ,fbox_bb=fbox_bb)

        else:
            gridfile = localdir + os.sep + "autoFillRecipeScripts/Mycoplasma/results/grid_store"
            env.placeMethod = "RAPID"
            env.saveResult = True
            env.innerGridMethod = "bhtree"  # jordan pure python ? sdf ?
            env.boundingBox = [[-2482, -2389.0, 100.0], [2495, 2466, 2181.0]]
            env.buildGrid(boundingBox=env.boundingBox, gridFileIn=gridfile, rebuild=True, gridFileOut=None, previousFill=False)
            env.fill5(verbose=0, usePP=False)

    except Exception as e:
        log.error("=============================================")
        if dbg:
            log.error("\n\n" + traceback.format_exc())
            log.error("=============================================")
        log.error("\n\n" + str(e) + "\n")
        log.error("=============================================")
        sys.exit(1)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()
