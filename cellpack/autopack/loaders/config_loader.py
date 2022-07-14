# -*- coding: utf-8 -*-
import os

import json
from json import encoder
encoder.FLOAT_REPR = lambda o: format(o, ".8g")


class ConfigLoader(object):
    def __init__(self, input_file_path):
        _, file_extension = os.path.splitext(input_file_path)
        self.file_path = input_file_path
        self.file_extension = file_extension
        self.config = self._read()

    def _read(self):
        """
        Read in a Json Config file.
        """
        config = json.load(open(self.file_path, "r"))
        return config
