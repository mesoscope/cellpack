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
import sys
import os
import re
import shutil
from os import path, environ

import ssl
import json

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

try:
    import urllib.request as urllib  # , urllib.parse, urllib.error
except ImportError:
    import urllib

packageContainsVFCommands = 1
ssl._create_default_https_context = ssl._create_unverified_context
use_json_hook = True
afdir = os.path.abspath(__path__[0])

# ==============================================================================
# #Setup autopack data directory.
# ==============================================================================
# the dir will have all the recipe + cache.
APPNAME = "autoPACK"
log = logging.getLogger("autopack")
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
if not os.path.exists(appdata):
    os.makedirs(appdata)
    log.info("autoPACK data dir created", appdata)

# ==============================================================================
# setup Panda directory
# ==============================================================================
# PANDA_PATH = ""
# if sys.platform == "darwin":
#     PANDA_PATH = afdir + os.sep + ".." + os.sep + "Panda3D"
#     sys.path.append("/Developer/Panda3D/")
#     sys.path.append("/Developer/Panda3D/lib/")  # in case already installed
#     # TODO need to fix the dependency that are locally set to /Developer/Panda3D/lib/
# elif sys.platform == "win32":
#     PANDA_PATH = afdir + os.sep + ".." + os.sep + "Panda3d-1.9.0-x64"
#     PANDA_PATH_BIN = PANDA_PATH + os.sep + "bin"
#     try:
#         if PANDA_PATH_BIN not in os.environ.get("PATH", ""):
#             os.environ["PATH"] = os.pathsep.join(
#                 (PANDA_PATH_BIN, os.environ.get("PATH", ""))
#             )
#     except Exception:
#         pass
#     sys.path.append(PANDA_PATH_BIN)
#     sys.path.append(PANDA_PATH)
# elif sys.platform == "linux2":  # linux ? blender and maya ?
#     PANDA_PATH = "/usr/lib/python2.7/dist-packages/"
#     PANDA_PATH_BIN = "/usr/lib/panda3d/"
# else:
#     pass
# sys.path.append(PANDA_PATH + os.sep + "lib")


def checkURL(URL):
    try:
        response = urllib.urlopen(URL)
    except Exception as e:
        log.error("Error in checkURL ", URL, e)
        return False
    return response.code != 404


# ==============================================================================
# setup the cache directory inside the app data folder
# ==============================================================================
cache_results = appdata + os.sep + "cache_results"
if not os.path.exists(cache_results):
    os.makedirs(cache_results)
cache_geoms = appdata + os.sep + "cache_geometries"
if not os.path.exists(cache_geoms):
    os.makedirs(cache_geoms)
cache_sphere = appdata + os.sep + "cache_collisionTrees"
if not os.path.exists(cache_sphere):
    os.makedirs(cache_sphere)
cache_recipes = appdata + os.sep + "cache_recipes"
if not os.path.exists(cache_recipes):
    os.makedirs(cache_recipes)

preferences = appdata + os.sep + "preferences"
if not os.path.exists(preferences):
    os.makedirs(preferences)
# we can now use some json/xml file for storing preferences and options.
# need others ?
cache_dir = {
    "geometries": cache_geoms,
    "results": cache_results,
    "collisionTrees": cache_sphere,
    "recipes": cache_recipes,
    "prefs": preferences,
}

usePP = False
helper = None
LISTPLACEMETHOD = ["jitter", "spheresBHT", "RAPID"]
try:
    from panda3d.core import Mat4  # noqa: F401

    LISTPLACEMETHOD = ["jitter", "spheresBHT", "pandaBullet", "RAPID"]
except ImportError:
    LISTPLACEMETHOD = ["jitter", "spheresBHT", "RAPID"]


ncpus = 2
# forceFetch is for any file not only recipe/ingredient etc...
forceFetch = False
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
recipe_web_pref_file = preferences + os.sep + "recipe_available.json"
recipe_user_pref_file = preferences + os.sep + "user_recipe_available.json"
recipe_dev_pref_file = preferences + os.sep + "autopack_serverDeveloper_recipeList.json"
autopack_path_pref_file = preferences + os.sep + "path_preferences.json"
autopack_user_path_pref_file = preferences + os.sep + "path_user_preferences.json"

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
        try:
            import urllib.request as urllib  # , urllib.parse, urllib.error
        except ImportError:
            import urllib
        if checkURL(fileName):
            urllib.urlretrieve(fileName, autopack_path_pref_file)
        else:
            log.error("problem accessing path %s", fileName)


# get user / default value
if not os.path.isfile(autopack_path_pref_file):
    log.error(autopack_path_pref_file + " file is not found")
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

replace_autoPACKserver = ["autoPACKserver", autoPACKserver]
replace_autopackdir = ["autopackdir", autopackdir]
replace_autopackdata = ["autopackdata", appdata]

replace_path = [replace_autoPACKserver, replace_autopackdir, replace_autopackdata]
global current_recipe_path
current_recipe_path = appdata
# we keep the file here, it come with the distribution
# wonder if the cache shouldn't use the version like other appDAta
# ie appData/AppName/Version/etc...
if not os.path.isfile(afdir + os.sep + "version.txt"):
    f = open(afdir + os.sep + "version.txt", "w")
    f.write("0.0.0")
    f.close()
f = open(afdir + os.sep + "version.txt", "r")
__version__ = f.readline()
f.close()

# should we check filespath

info_dic = ["setupfile", "resultfile", "wrkdir"]
# change the setupfile access to online in recipe_available.xml
# change the result access to online in recipe_available.xml

# hard code recipe here is possible
global RECIPES
RECIPES = OrderedDict()


USER_RECIPES = {}


def resetDefault():
    if os.path.isfile(autopack_user_path_pref_file):
        os.remove(autopack_user_path_pref_file)


def revertOnePath(p):
    for v in replace_path:
        p = p.replace(v[1], v[0])
    return p


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


def fixOnePath(p):
    for v in replace_path:
        # fix before
        if fixpath and re.findall("{0}".format(re.escape(v[0])), p):
            p = checkErrorInPath(p, v[1])
            # check for legacyServerautoPACK_database_1.0.0
            p = checkErrorInPath(p, "autoPACK_database_1.0.0")
        p = p.replace(v[0], v[1])
    return p


def updateReplacePath(newPaths):
    for w in newPaths:
        found = False
        for i, v in enumerate(replace_path):
            if v[0] == w[0]:
                replace_path[i][1] = w[1]
                found = True
        if not found:
            replace_path.append(w)


def retrieveFile(filename, destination="", cache="geometries", force=None):
    #    helper = autopack.helper
    if force is None:
        force = forceFetch
    if filename.find("http") == -1 and filename.find("ftp") == -1:
        filename = fixOnePath(filename)
    log.info("autopack retrieve file %s", filename)
    if filename.find("http") != -1 or filename.find("ftp") != -1:
        # check if using autoPACKserver
        useAPServer = False
        if filename.find(autoPACKserver) != -1:
            useAPServer = True
        reporthook = None
        if helper is not None:
            reporthook = helper.reporthook
        name = filename.split("/")[-1]  # the recipe name
        tmpFileName = cache_dir[cache] + os.sep + destination + name
        if not os.path.exists(cache_dir[cache] + os.sep + destination):
            os.makedirs(cache_dir[cache] + os.sep + destination)
        # check if exist first
        if not os.path.isfile(tmpFileName) or force:
            if checkURL(filename):
                try:
                    urllib.urlretrieve(filename, tmpFileName, reporthook=reporthook)
                except Exception as e:
                    log.error("error fetching file %r", e)
                    if useAPServer:
                        log.info("try alternate server")
                        urllib.urlretrieve(
                            autoPACKserver_alt + "/" + cache + "/" + name,
                            tmpFileName,
                            reporthook=reporthook,
                        )
            else:
                if not os.path.isfile(tmpFileName):
                    log.error("not isfile %s", tmpFileName)
                    return None
        filename = tmpFileName
        log.info("autopack return grabbed %s", filename)
        # check the file is not an error
        return filename
    # if no folder provided, use the current_recipe_folder
    if os.path.isfile(cache_dir[cache] + os.sep + filename):
        return cache_dir[cache] + os.sep + filename
    if os.path.isfile(current_recipe_path + os.sep + filename):
        return current_recipe_path + os.sep + filename
    if checkURL(autoPACKserver + "/" + cache + "/" + filename):
        reporthook = None
        if helper is not None:
            reporthook = helper.reporthook
        name = filename.split("/")[-1]  # the recipe name
        tmpFileName = cache_dir[cache] + os.sep + destination + name
        try:
            urllib.urlretrieve(
                autoPACKserver + "/" + cache + "/" + filename,
                tmpFileName,
                reporthook=reporthook,
            )
            return tmpFileName
        except:  # noqa: E722
            urllib.urlretrieve(
                autoPACKserver_alt + "/" + cache + "/" + filename,
                tmpFileName,
                reporthook=reporthook,
            )
            # check the file is not an error
            return tmpFileName
    if checkURL(autoPACKserver_alt + "/" + cache + "/" + filename):
        reporthook = None
        if helper is not None:
            reporthook = helper.reporthook
        name = filename.split("/")[-1]  # the recipe name
        tmpFileName = cache_dir[cache] + os.sep + destination + name
        try:
            urllib.urlretrieve(
                autoPACKserver_alt + "/" + cache + "/" + filename,
                tmpFileName,
                reporthook=reporthook,
            )
        except:  # noqa: E722
            return None
        # check the file is not an error
        return tmpFileName
    log.error("not found %s", filename)
    return filename


def fixPath(adict):  # , k, v):
    for key in list(adict.keys()):
        if type(adict[key]) is dict or type(adict[key]) is OrderedDict:
            fixPath(adict[key])
        else:
            #        if key == k:
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
    replace_autoPACKserver[1] = autoPACKserver
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
            replace_autopackdir[1] = pref_path["autopackdir"]


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
    if checkURL(fname):
        urllib.urlretrieve(fname, recipe_web_pref_file)
    else:
        print("problem accessing recipe " + fname)


def updateRecipAvailableJSON(recipesfile):
    if not os.path.isfile(recipesfile):
        print(recipesfile + " was not found")
        return
    # replace shortcut pathby hard path
    f = open(recipesfile, "r")
    if use_json_hook:
        recipes = json.load(f, object_pairs_hook=OrderedDict)
    else:
        recipes = json.load(f)
    f.close()
    RECIPES.update(recipes)
    log.info("recipes updated %d" + str(len(RECIPES)))


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
                        text = afdir + os.sep + text
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
                        text = afdir + os.sep + text
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
                    text = afdir + os.sep + text
                RECIPES[name][version][info] = str(text)
    log.info("recipes updated %d" + str(len(RECIPES)))


def updateRecipAvailable(recipesfile):
    if not os.path.isfile(recipesfile):
        return
    # check format xml or json
    fileName, fileExtension = os.path.splitext(recipesfile)
    if fileExtension.lower() == ".xml":
        updateRecipAvailableXML(recipesfile)
    elif fileExtension.lower() == ".json":
        updateRecipAvailableJSON(recipesfile)
    fixPath(RECIPES)
    #    fixPath(RECIPES,"wrkdir")#or autopackdata
    #    fixPath(RECIPES,"resultfile")
    log.info("recipes updated and path fixed %d" + str(len(RECIPES)))


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

log.info("currently nb recipes is %s" + str(len(RECIPES)))
# check cache directory create if doesnt exit.abs//should be in user pref?
# ?
# need a distinction between autopackdir and cachdir
wkr = afdir
# in the predefined working directory

BD_BOX_PATH = "/home/ludo/Tools/bd_box-2.2"  # or /Users/ludo/DEV/bd_box-2.1/
GMODE = "Simple"
