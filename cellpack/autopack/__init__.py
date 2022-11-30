# -*- coding: utf-8 -*-
"""
Created on Fri Jul 20 23:53:00 2012
###############################################################################
#
# autoPACK Authors: Graham T. Johnson, Mostafa Al-Alusi, Ludovic Autin, Michel Sanner
#   Based on COFFEE Script developed by Graham Johnson between 2005 and 2010
#   with assistance from Mostafa Al-Alusi in 2009 and periodic input
#   from Arthur Olson's Molecular Graphics Lab
#
# __init__.py Authors: Ludovic Autin with minor editing/enhancement from Graham Johnson
#
# Copyright: Graham Johnson ©2010
#
# This file "__init__.py" is part of autoPACK.
#
#    autoPACK is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    autoPACK is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with autoPACK (See "CopyingGNUGPL" in the installation.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
Name: 'autoPACK'
Define here some usefull variable and setup filename path that facilitate
AF
@author: Ludovic Autin with editing by Graham Johnson
"""
import logging
import logging.config
import sys
import os
import re
import shutil
from os import path, environ
from pathlib import Path
import urllib.request as urllib

import ssl
import json

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

packageContainsVFCommands = 1
ssl._create_default_https_context = ssl._create_unverified_context
use_json_hook = True
afdir = Path(os.path.abspath(__path__[0]))

###############################################################################
log_file_path = path.join(path.dirname(path.abspath(__file__)), "../../logging.conf")
logging.config.fileConfig(log_file_path, disable_existing_loggers=False)
log = logging.getLogger("autopack")
log.propagate = False
###############################################################################


def make_directory_if_needed(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


# ==============================================================================
# #Setup autopack data directory.
# ==============================================================================
# the dir will have all the recipe + cache.


APPNAME = "autoPACK"
# log = logging.getLogger("autopack")
# log.propagate = False

if sys.platform == "darwin":
    # from AppKit import NSSearchPathForDirectoriesInDomains
    # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
    # NSApplicationSupportDirectory = 14
    # NSUserDomainMask = 1
    # True for expanding the tilde into a fully qualified path
    # appdata = path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APPNAME)
    appdata = os.path.expanduser("~") + "/Library/Application Support/autoPACK"
elif sys.platform == "win32":
    appdata = path.join(environ["APPDATA"], APPNAME)
else:
    appdata = path.expanduser(path.join("~", "." + APPNAME))
make_directory_if_needed(appdata)
log.info("autoPACK data dir created", appdata)

appdata = Path(appdata)


def url_exists(url):
    try:
        response = urllib.urlopen(url)
    except Exception:
        return False
    return response.code != 404


# ==============================================================================
# setup the cache directory inside the app data folder
# ==============================================================================


cache_results = appdata / "cache_results"
cache_geoms = appdata / "cache_geometries"
cache_sphere = appdata / "cache_collisionTrees"
cache_recipes = appdata / "cache_recipes"
preferences = appdata / "preferences"
# we can now use some json/xml file for storing preferences and options.
# need others ?
cache_dir = {
    "geometries": cache_geoms,
    "results": cache_results,
    "collisionTrees": cache_sphere,
    "recipes": cache_recipes,
    "prefs": preferences,
}

for _, dir in cache_dir.items():
    make_directory_if_needed(dir)

usePP = False
helper = None
LISTPLACEMETHOD = ["jitter", "spheresBHT"]
try:
    from panda3d.core import Mat4  # noqa: F401

    LISTPLACEMETHOD = ["jitter", "spheresBHT", "pandaBullet"]
except ImportError:
    LISTPLACEMETHOD = ["jitter", "spheresBHT"]


ncpus = 2
checkAtstartup = True
testPeriodicity = False
biasedPeriodicity = None  # [1,1,1]
fixpath = False
verbose = 0
messag = """Welcome to autoPACK.
Please update to the latest version under the Help menu.
"""

# we have to change the name of theses files. and decide how to handle the
# currated recipeList, and the dev recipeList
# same for output and write theses file see below for the cache directories
# all theses file will go in the pref folder ie cache_path
recipe_web_pref_file = preferences / "recipe_available.json"
recipe_user_pref_file = preferences / "user_recipe_available.json"
recipe_dev_pref_file = preferences / "autopack_serverDeveloper_recipeList.json"
autopack_path_pref_file = preferences / "path_preferences.json"
autopack_user_path_pref_file = preferences / "path_user_preferences.json"

# Default values
autoPACKserver = (
    "https://cdn.rawgit.com/mesoscope/cellPACK_data/master/cellPACK_database_1.1.0"
)
autoPACKserver_default = "https://cdn.rawgit.com/mesoscope/cellPACK_data/master/cellPACK_database_1.1.0"  # XML # noqa: E501
autoPACKserver_alt = "http://mgldev.scripps.edu/projects/autoPACK/data/cellPACK_data/cellPACK_database_1.1.0"  # noqa: E501
filespath = (
    "https://cdn.rawgit.com/mesoscope/cellPACK_data/master/autoPACK_filePaths.json"
)
recipeslistes = autoPACKserver + "/autopack_recipe.json"

autopackdir = str(afdir)  # copy


def checkPath():
    fileName = filespath  # autoPACKserver+"/autoPACK_filePaths.json"
    if fileName.find("http") != -1 or fileName.find("ftp") != -1:
        if url_exists(fileName):
            urllib.urlretrieve(fileName, autopack_path_pref_file)
        else:
            log.error("problem accessing path %s", fileName)


# get user / default value
if not os.path.isfile(autopack_path_pref_file):
    log.error(str(autopack_path_pref_file) + "file is not found")
    checkPath()

doit = False
if os.path.isfile(autopack_user_path_pref_file):
    f = open(autopack_user_path_pref_file, "r")
    doit = True
elif os.path.isfile(autopack_path_pref_file):
    f = open(autopack_path_pref_file, "r")
    doit = True
if doit:
    log.info("autopack_path_pref_file %s", autopack_path_pref_file)
    pref_path = json.load(f)
    f.close()
    if "autoPACKserver" not in pref_path:
        log.warning("problem with autopack_path_pref_file %s", autopack_path_pref_file)
    else:
        autoPACKserver = pref_path["autoPACKserver"]
        if "filespath" in pref_path:
            if pref_path["filespath"] != "default":
                filespath = pref_path["filespath"]
        if "recipeslistes" in pref_path:
            if pref_path["recipeslistes"] != "default":
                recipeslistes = pref_path["recipeslistes"]
        if "autopackdir" in pref_path:
            if pref_path["autopackdir"] != "default":
                autopackdir = pref_path["autopackdir"]

REPLACE_PATH = {
    "autoPACKserver": autoPACKserver,
    "autopackdir": autopackdir,
    "autopackdata": appdata,
}

global CURRENT_RECIPE_PATH
CURRENT_RECIPE_PATH = appdata
# we keep the file here, it come with the distribution
# wonder if the cache shouldn't use the version like other appDAta
# ie appData/AppName/Version/etc...
if not os.path.isfile(afdir / "version.txt"):
    f = open(afdir / "version.txt", "w")
    f.write("0.0.0")
    f.close()
f = open(afdir / "version.txt", "r")
__version__ = f.readline()
f.close()

# should we check filespath

info_dic = ["setupfile", "result_file", "wrkdir"]
# change the setupfile access to online in recipe_available.xml
# change the result access to online in recipe_available.xml

# hard code recipe here is possible
global RECIPES
RECIPES = OrderedDict()


USER_RECIPES = {}


def resetDefault():
    if os.path.isfile(autopack_user_path_pref_file):
        os.remove(autopack_user_path_pref_file)


def checkErrorInPath(p, toreplace):
    # if in p we already have part of the replace path
    part = p.split(os.sep)
    newpath = ""
    for i, e in enumerate(part):
        f = re.findall("{0}".format(re.escape(e)), toreplace)
        if not len(f):
            newpath += e + "/"
    if part[0] == "http:":
        newpath = "http://" + newpath[6:]
    return newpath[:-1]


def fixOnePath(path):
    path = str(path)
    for old_value, new_value in REPLACE_PATH.items():
        # fix before
        new_value = str(new_value)
        if fixpath and re.findall("{0}".format(re.escape(old_value)), path):
            path = checkErrorInPath(path, new_value)
            # check for legacyServerautoPACK_database_1.0.0
            path = checkErrorInPath(path, "autoPACK_database_1.0.0")
        path = path.replace(old_value, new_value)
    return path


def updateReplacePath(newPaths):
    for w in newPaths:
        found = False
        for i, v in enumerate(REPLACE_PATH):
            if v[0] == w[0]:
                REPLACE_PATH[i][1] = w[1]
                found = True
        if not found:
            REPLACE_PATH.append(w)


def download_file(url, local_file_path, reporthook):
    if url_exists(url):
        try:
            urllib.urlretrieve(url, local_file_path, reporthook=reporthook)
        except Exception as e:
            log.error(f"error fetching file {e}, {url}")
    else:
        raise Exception(f"Url does not exist {url}")


def is_full_url(file_path):
    return file_path.find("http") != -1 or file_path.find("ftp") != -1

def is_remote_path(file_path):
    return ":" in file_path;

def retrieve_file(filename, destination="", cache="geometries", force=False):
    """
    Options:
    1. Find file locally, return the file path
    2. Download file to local cache, return path (might involve replacing short-code in url)
    3. Force download even though you have a local copy

    Returns location of file (either already there or newly downloaded)
    """
    local_file_path = filename

    if is_remote_path(filename):
        # deal with remote db
        # get url from path
        if is_full_url(str(filename)):
            url = filename
            reporthook = None
            if helper is not None:
                reporthook = helper.reporthook

        name = url.split("/")[-1]  # the recipe name
        local_file_directory = cache_dir[cache] / destination
        local_file_path = local_file_directory / name
        make_directory_if_needed(local_file_directory)
        # check if exist first
        if not os.path.isfile(local_file_path) or force:
            download_file(url, local_file_path, reporthook)
        log.info(f"autopack downloaded and stored file: {local_file_path}")
        return local_file_path
    filename = Path(filename)
    if os.path.isfile(cache_dir[cache] / filename):
        return cache_dir[cache] / filename
    if os.path.isfile(CURRENT_RECIPE_PATH / filename):
        # if no folder provided, use the current_recipe_folder
        return CURRENT_RECIPE_PATH / filename

    url = autoPACKserver + "/" + str(cache) + "/" + str(filename)
    if url_exists(url):
        reporthook = None
        if helper is not None:
            reporthook = helper.reporthook
        name = filename
        local_file_path = cache_dir[cache] / destination / name
        download_file(url, local_file_path, reporthook)
        return local_file_path
    return filename


def load_file(filename, destination="", cache="geometries", force=None):
    local_file_path = retrieve_file(
        filename, destination=destination, cache=cache, force=force
    )
    return json.load(open(local_file_path, "r"))


def fixPath(adict):  # , k, v):
    for key in list(adict.keys()):
        if type(adict[key]) is dict or type(adict[key]) is OrderedDict:
            fixPath(adict[key])
        else:
            # if key == k:
            adict[key] = fixOnePath(adict[key])


def updatePathJSON():
    if not os.path.isfile(autopack_path_pref_file):
        log.error(autopack_path_pref_file + " file is not found")
        return
    if os.path.isfile(autopack_user_path_pref_file):
        f = open(autopack_user_path_pref_file, "r")
    else:
        f = open(autopack_path_pref_file, "r")
    pref_path = json.load(f)
    f.close()
    autoPACKserver = pref_path["autoPACKserver"]
    REPLACE_PATH["autoPACKserver"] = autoPACKserver
    filespath = autoPACKserver + "/autoPACK_filePaths.json"
    if "filespath" in pref_path:
        if pref_path["filespath"] != "default":
            filespath = pref_path["filespath"]  # noqa: F841
    recipeslistes = autoPACKserver + "/autopack_recipe.json"
    if "recipeslistes" in pref_path:
        if pref_path["recipeslistes"] != "default":
            recipeslistes = pref_path["recipeslistes"]  # noqa: F841
    if "autopackdir" in pref_path:
        if pref_path["autopackdir"] != "default":
            autopackdir = pref_path["autopackdir"]  # noqa: F841
            REPLACE_PATH["autoPACKserver"] = pref_path["autopackdir"]


def updatePath():
    # now get it
    fileName, fileExtension = os.path.splitext(autopack_path_pref_file)
    if fileExtension.lower() == ".xml":
        pass  # updateRecipAvailableXML(recipesfile)
    elif fileExtension.lower() == ".json":
        updatePathJSON()


def checkRecipeAvailable():
    fname = fixOnePath(recipeslistes)  # autoPACKserver+"/autopack_recipe.json"
    try:
        import urllib.request as urllib  # , urllib.parse, urllib.error
    except ImportError:
        import urllib
    if url_exists(fname):
        urllib.urlretrieve(fname, recipe_web_pref_file)
    else:
        print("problem accessing recipe " + fname)


def updateRecipeAvailableJSON(recipesfile):
    if not os.path.isfile(recipesfile):
        print(recipesfile + " was not found")
        return
    # replace shortcut pathby hard path
    f = open(recipesfile, "r")
    # if use_json_hook:
    #     recipes = json.load(f, object_pairs_hook=OrderedDict)
    # else:
    #     recipes = json.load(f)
    f.close()
    log.info(f"recipes updated {len(RECIPES)}")


def updateRecipAvailableXML(recipesfile):
    if not os.path.isfile(recipesfile):
        return
    from xml.dom.minidom import parse

    XML = parse(recipesfile)  # parse an XML file by name
    res = XML.getElementsByTagName("recipe")
    for r in res:
        name = r.getAttribute("name")
        version = r.getAttribute("version")
        if name in RECIPES:  # update te value
            if version in RECIPES[name]:
                for info in info_dic:
                    text = (
                        r.getElementsByTagName(info)[0]
                        .childNodes[0]
                        .data.strip()
                        .replace("\t", "")
                    )
                    if text[0] != "/" and text.find("http") == -1:
                        text = afdir / text
                    RECIPES[name][version][info] = str(text)
            else:
                RECIPES[name][version] = {}
                for info in info_dic:
                    text = (
                        r.getElementsByTagName(info)[0]
                        .childNodes[0]
                        .data.strip()
                        .replace("\t", "")
                    )
                    if text[0] != "/" and text.find("http") == -1:
                        text = afdir / text
                    RECIPES[name][version][info] = str(text)
        else:  # append to the dictionary
            RECIPES[name] = {}
            RECIPES[name][version] = {}
            for info in info_dic:
                text = (
                    r.getElementsByTagName(info)[0]
                    .childNodes[0]
                    .data.strip()
                    .replace("\t", "")
                )
                if text[0] != "/" and text.find("http") == -1:
                    text = afdir / text
                RECIPES[name][version][info] = str(text)
    log.info(f"recipes updated {RECIPES}")


def updateRecipAvailable(recipesfile):
    if not os.path.isfile(recipesfile):
        return
    # check format xml or json
    fileName, fileExtension = os.path.splitext(recipesfile)
    if fileExtension.lower() == ".xml":
        updateRecipAvailableXML(recipesfile)
    elif fileExtension.lower() == ".json":
        updateRecipeAvailableJSON(recipesfile)
    fixPath(RECIPES)
    #    fixPath(RECIPES,"wrkdir")#or autopackdata
    #    fixPath(RECIPES,"resultfile")
    log.info(f"recipes updated and path fixed {RECIPES}")


def saveRecipeAvailable(recipe_dictionary, recipefile):
    from xml.dom.minidom import getDOMImplementation

    impl = getDOMImplementation()
    XML = impl.createDocument(None, "autoPACK_recipe", None)
    root = XML.documentElement
    for k in recipe_dictionary:
        for v in recipe_dictionary[k]:
            relem = XML.createElement("recipe")
            relem.setAttribute("name", k)
            relem.setAttribute("version", v)
            root.appendChild(relem)
            for l in recipe_dictionary[k][v]:  # noqa: E741
                node = XML.createElement(l)
                data = XML.createTextNode(recipe_dictionary[k][v][l])
                node.appendChild(data)
                relem.appendChild(node)
    f = open(recipefile, "w")
    XML.writexml(f, indent="\t", addindent="", newl="\n")
    f.close()


def saveRecipeAvailableJSON(recipe_dictionary, filename):
    with open(filename, "w") as fp:  # doesnt work with symbol link ?
        json.dump(
            recipe_dictionary, fp, indent=1, separators=(",", ": ")
        )  # ,indent=4, separators=(',', ': ')


def clearCaches(*args):
    # can't work if file are open!
    for k in cache_dir:
        try:
            shutil.rmtree(cache_dir[k])
            os.makedirs(cache_dir[k])
        except:  # noqa: E722
            print("problem cleaning ", cache_dir[k])


# we should read a file to fill the RECIPE Dictionary
# so we can add some and write/save setup
# afdir  or user_pref

if checkAtstartup:
    checkPath()
    updatePathJSON()
    log.info("path are updated ")

if checkAtstartup:
    # get from server the list of recipe
    # recipe_web_pref_file
    checkRecipeAvailable()
    updateRecipAvailable(recipe_web_pref_file)
    updateRecipAvailable(recipe_user_pref_file)
    updateRecipAvailable(recipe_dev_pref_file)

log.info(f"currently number recipes is {len(RECIPES)}")
# check cache directory create if doesnt exit.abs//should be in user pref?
# ?
# need a distinction between autopackdir and cachdir
wkr = afdir
# in the predefined working directory

BD_BOX_PATH = "/home/ludo/Tools/bd_box-2.2"  # or /Users/ludo/DEV/bd_box-2.1/
GMODE = "Simple"
