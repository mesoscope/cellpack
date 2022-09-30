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
import json
import argparse

# Relative
from cellpack import get_module_version
from cellpack.autopack.Environment import Environment
import cellpack.autopack.Analysis as analysis

###############################################################################
log_file_path = path.join(path.dirname(path.abspath(__file__)), "../../logging.conf")
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger()
###############################################################################


class Args(argparse.Namespace):

    DEFAULT_INPUT_FOLDER = "out/analyze/test_analyze/jitter/"
    DEFAULT_OUTPUT_FOLDER = "out/analyze/test_analyze/jitter/"

    def __init__(self):
        # Arguments that could be passed in through the command line
        self.input = self.DEFAULT_INPUT_FOLDER
        self.output = self.DEFAULT_OUTPUT_FOLDER
        self.debug = True
        #
        self.__parse()

    def __parse(self):
        p = argparse.ArgumentParser(
            prog="analyze",
            description="Analyze packings from cellPACK",
        )

        p.add_argument(
            "-v",
            "--version",
            action="version",
            version="%(prog)s " + get_module_version(),
        )
        p.add_argument(
            "-i",
            "--input",
            action="store",
            dest="input",
            type=str,
            default=self.input,
            help="Relative path to the folder containing cellPACK packing outputs",
        )
        p.add_argument(
            "-o",
            "--output",
            action="store",
            dest="output",
            type=str,
            default=self.output,
            help="Relative path to the folder to store outputs from the analysis",
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
        input_path = os.path.join(os.getcwd(), args.input)
        output_path = args.output
        os.makedirs(output_path, exist_ok=True)
        log.info("Input : {}\n".format(args.recipe))
        
        all_pos_file = path.abspath(path.join(input_path, "all_positions.json"))
        with open(all_pos_file, 'r') as j:
            all_pos = json.loads(j.read())

        all_objs = analysis.get_xyz_dict_from_all_pos_dict(all_pos)


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
