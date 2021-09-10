#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run autopack from recipe file
"""

# Standard library
import sys
import os
from os import path
import logging
import traceback

# Third party
import numpy
import argparse

# Relative
import cellpack.autopack.upy as upy
from cellpack import autopack, get_module_version
from cellpack.autopack.Environment import Environment
from cellpack.autopack.Analysis import AnalyseAP

###############################################################################

log_file_path = path.join(path.dirname(path.abspath(__file__)), "../../logging.conf")
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)

log = logging.getLogger("root")
###############################################################################


class Args(argparse.Namespace):

    DEFAULT_DIM = 2
    DEFAULT_ANALYSIS = True
    DEFAULT_RECIPE_FILE = "cellpack/test-recipes/NM_Analysis_FigureA1.0.xml"
    DEFAULT_OUTPUT_FILE = "/Users/meganriel-mehan/Dropbox/cellPack/NM_Analysis_A2_2/"
    DEFAULT_PLACE_METHOD = "RAPID"

    def __init__(self):
        # Arguments that could be passed in through the command line
        self.dim = self.DEFAULT_DIM
        self.analysis = self.DEFAULT_ANALYSIS
        self.recipe = self.DEFAULT_RECIPE_FILE
        self.output = self.DEFAULT_OUTPUT_FILE
        self.place_method = self.DEFAULT_PLACE_METHOD
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
            dest="recipe",
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
            "-d",
            "--dim",
            action="store",
            dest="dim",
            type=int,
            default=self.dim,
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
            "-p",
            "--place-method",
            action="store",
            dest="place_method",
            type=str,
            default=self.place_method,
            help="The place method",
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
        recipe_path = os.path.join(os.getcwd(), args.recipe)
        do_analysis = args.analysis
        output = args.output
        if os.path.isdir(output) is False:
            os.mkdir(output)
        dim = args.dim
        place_method = args.place_method
        print("Recipe : {}\n".format(args.recipe))
        localdir = wrkDir = autopack.__path__[0]
        helperClass = upy.getHelperClass()
        helper = helperClass(vi="nogui")
        print("HELPER", helper)

        autopack.helper = helper

        fileName = os.path.basename(recipe_path)
        env = Environment(name=fileName)

        env.helper = helper
        env.load_recipe(recipe_path)
        afviewer = None

        env.saveResult = False

        def setCompartment(ingr):
            # ingr.rejectionThreshold = 60  # [1,1,0]#
            ingr.nbJitter = 6
            ingr.rejectionThreshold = 100  # [1,1,0]#
            ingr.cutoff_boundary = 0  # ingr.encapsulatingRadius/2.0
            if dim == 3:
                ingr.jitterMax = [1, 1, 1]
            else:
                ingr.jitterMax = [1, 1, 0]

        env.loopThroughIngr(setCompartment)

        if do_analysis:
            log.info("DOING ANALYSIS %b", do_analysis)
            if place_method == "RAPID":
                env.placeMethod = "RAPID"
                env.encapsulatingGrid = 0
                autopack.testPeriodicity = False
                analyse = AnalyseAP(env=env, viewer=afviewer, result_file=None)
                analyse.g.Resolution = 1.0
                env.boundingBox = numpy.array(env.boundingBox)
                log.info("bounding box %r", env.boundingBox)

                analyse.doloop(
                    1,
                    env.boundingBox,
                    wrkDir,
                    output,
                    rdf=True,
                    render=False,
                    twod=(dim == 2),
                    use_file=True,
                )  # ,fbox_bb=fbox_bb)
            elif place_method == "pandaBullet":
                env.placeMethod = "pandaBullet"
                env.encapsulatingGrid = 0
                env.use_periodicity = True
                autopack.testPeriodicity = True
                autopack.biasedPeriodicity = [1, 1, 1]
                analyse = AnalyseAP(env=env, viewer=afviewer, result_file=None)
                analyse.g.Resolution = 1.0
                env.smallestProteinSize = 30.0  # get it faster? same result ?
                env.boundingBox = numpy.array([[0, 0, 0], [1000.0, 1000.0, 15.0]])
                log.info("bounding box %r", env.boundingBox)
                analyse.doloop(
                    1,
                    env.boundingBox,
                    wrkDir,
                    output,
                    rdf=True,
                    render=False,
                    twod=(dim == 2),
                    use_file=True,
                )  # ,fbox_bb=fbox_bb)
            else:
                env.placeMethod = place_method
                env.encapsulatingGrid = 0
                autopack.testPeriodicity = False
                analyse = AnalyseAP(env=env, viewer=afviewer, result_file=None)
                analyse.g.Resolution = 1.0
                env.boundingBox = numpy.array(env.boundingBox)

                analyse.doloop(
                    2,
                    env.boundingBox,
                    wrkDir,
                    output,
                    rdf=True,
                    render=False,
                    twod=(dim == 2),
                    use_file=True,
                )  # ,fbox_bb=fbox_bb)
        else:
            gridfile = (
                localdir
                + os.sep
                + "autoFillRecipeScripts/Mycoplasma/results/grid_store"
            )
            env.placeMethod = "RAPID"
            env.saveResult = True
            env.innerGridMethod = "jordan"  # jordan pure python ? sdf ?
            env.boundingBox = [[-2482, -2389.0, 100.0], [2495, 2466, 2181.0]]
            env.buildGrid(
                boundingBox=env.boundingBox,
                gridFileIn=gridfile,
                rebuild=True,
                gridFileOut=None,
                previousFill=False,
            )
            env.pack_grid(verbose=0, usePP=False)

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
