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
import logging.config
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
log = logging.getLogger()
###############################################################################


class Args(argparse.Namespace):

    DEFAULT_DIM = 2
    DEFAULT_ANALYSIS = True
    DEFAULT_RECIPE_FILE = "cellpack/test-recipes/NM_Analysis_FigureB1.0.json"
    DEFAULT_OUTPUT_FOLDER = "/Users/meganriel-mehan/Dropbox/cellPack/"
    DEFAULT_PLACE_METHODS = [
        "jitter",
        "RAPID",
        "pandaBulletRelax",
        "pandaBullet",
        "spheresBHT",
    ]

    def __init__(self):
        # Arguments that could be passed in through the command line
        self.dim = self.DEFAULT_DIM
        self.analysis = self.DEFAULT_ANALYSIS
        self.recipe = self.DEFAULT_RECIPE_FILE
        self.output = self.DEFAULT_OUTPUT_FOLDER
        self.place_methods = self.DEFAULT_PLACE_METHODS
        self.save_analysis_plot = None
        self.grid_plot = None
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
            help="Full path to the folder where to store the results file",
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
            "-na",
            "--no-analysis",
            action="store_false",
            dest="analysis",
            default=self.analysis,
            help="Turn off analysis script",
        )
        p.add_argument(
            "-p",
            "--place-methods",
            action="store",
            dest="place_methods",
            nargs="+",
            default=self.place_methods,
            help="The place methods to test, can be an array",
        )
        p.add_argument(
            "-np",
            "--no-plot",
            action="store_false",
            dest="save_analysis_plot",
            default=self.dim == 2 and self.analysis,
            help="Turn off the save plot function, defaults to True if analysis is True and 2D",
        )
        p.add_argument(
            "-ng",
            "--no-grid-plot",
            action="store_false",
            dest="grid_plot",
            default=self.dim == 2 and self.analysis,
            help="Turn off plotly plot, defaults to True if analysis is True and 2D",
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
        dim = args.dim
        default_should_plot = args.dim == 2 and do_analysis
        save_plot = (
            args.save_analysis_plot
            if args.save_analysis_plot is not None
            else default_should_plot
        )
        show_plotly_plot = (
            args.grid_plot if args.grid_plot is not None else default_should_plot
        )
        output = args.output
        if os.path.isdir(output) is False:
            os.mkdir(output)
        log.info("Recipe : {}\n".format(args.recipe))
        helperClass = upy.getHelperClass()
        helper = helperClass(vi="nogui")

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
            for place_method in args.place_methods:
                log.info(f"starting {place_method}")
                env.placeMethod = place_method
                env.encapsulatingGrid = 0
                analyse = AnalyseAP(env=env, viewer=afviewer, result_file=None)
                analyse.g.Resolution = 1.0
                env.boundingBox = numpy.array(env.boundingBox)
                output_folder = os.path.join(args.output, env.name)
                if os.path.isdir(output_folder) is False:
                    os.mkdir(output_folder)
                output = os.path.join(output_folder, place_method)
                if os.path.isdir(output) is False:
                    os.mkdir(output)
                log.info(f"saving to {output}")
                analyse.doloop(
                    1,
                    env.boundingBox,
                    output,
                    plot=save_plot,
                    show_plotly_plot=show_plotly_plot,
                    twod=(dim == 2),
                )
        else:
            for place_method in args.place_methods:
                env.placeMethod = place_method
                env.saveResult = True
                env.innerGridMethod = "jordan"  # jordan pure python ? sdf ?
                env.boundingBox = [[-2482, -2389.0, 100.0], [2495, 2466, 2181.0]]
                env.buildGrid(
                    boundingBox=env.boundingBox,
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
