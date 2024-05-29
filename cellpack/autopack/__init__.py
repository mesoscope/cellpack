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
import os
import re
import shutil
import getpass
from pathlib import Path
import urllib.request as urllib
from collections import OrderedDict
import ssl
import json
from cellpack.autopack.DBRecipeHandler import DBRecipeLoader
from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS

from cellpack.autopack.loaders.utils import read_json_file, write_json_file
import boto3
import botocore

packageContainsVFCommands = 1
ssl._create_default_https_context = ssl._create_unverified_context
use_json_hook = True
afdir = Path(os.path.abspath(__path__[0]))
os.environ["NUMEXPR_MAX_THREADS"] = "32"

###############################################################################
log_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../logging.conf"
)
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
appdata = Path(__file__).parents[2] / ".cache"
make_directory_if_needed(appdata)
log.info(f"cellPACK data dir created {appdata}")
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

cache_results = appdata / "results"
cache_geoms = appdata / "geometries"
cache_sphere = appdata / "collisionTrees"
cache_recipes = appdata / "recipes"
cache_grids = appdata / "grids"
preferences = appdata / "preferences"
# we can now use some json/xml file for storing preferences and options.
# need others ?
CACHE_DIR = {
    "geometries": cache_geoms,
    "results": cache_results,
    "collisionTrees": cache_sphere,
    "recipes": cache_recipes,
    "grids": cache_grids,
    "prefs": preferences,
}

for _, dir in CACHE_DIR.items():
    make_directory_if_needed(dir)

usePP = False
helper = None
ncpus = 2
checkAtstartup = True
testPeriodicity = False
biasedPeriodicity = None  # [1,1,1]

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
autoPACKserver_alt = "http://mgldev.scripps.edu/projects/autoPACK/data/cellPACK_data/cellPACK_database_1.1.0"  # noqa: E501
filespath = (
    "https://cdn.rawgit.com/mesoscope/cellPACK_data/master/autoPACK_filePaths.json"
)
list_of_available_recipes = "github:autopack_recipe.json"

autopackdir = str(afdir)  # copy


def checkPath():
    fileName = filespath  # autoPACKserver+"/autoPACK_filePaths.json"
    if fileName.find("http") != -1 or fileName.find("ftp") != -1:
        if url_exists(fileName):
            urllib.urlretrieve(fileName, autopack_path_pref_file)
        else:
            log.error(f"problem accessing path {fileName}")


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
    log.info(f"autopack_path_pref_file {autopack_path_pref_file}")
    pref_path = json.load(f)
    f.close()
    if "autoPACKserver" not in pref_path:
        log.warning(f"problem with autopack_path_pref_file {autopack_path_pref_file}")
    else:
        autoPACKserver = pref_path["autoPACKserver"]
        if "filespath" in pref_path:
            if pref_path["filespath"] != "default":
                filespath = pref_path["filespath"]
        if "autopackdir" in pref_path:
            if pref_path["autopackdir"] != "default":
                autopackdir = pref_path["autopackdir"]


REPLACE_PATH = {
    "autoPACKserver": autoPACKserver,
    "autopackdir": autopackdir,
    "autopackdata": appdata,
    f"{DATABASE_IDS.GITHUB}:": autoPACKserver,
    f"{DATABASE_IDS.FIREBASE}:": None,
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
        path = path.replace(old_value, new_value)
    return path


def updateReplacePath(newPaths):
    for w in newPaths:
        REPLACE_PATH[w[0]] = w[1]


def download_file_from_s3(s3_uri, local_file_path):
    s3_client = boto3.client("s3")
    bucket_name, key = parse_s3_uri(s3_uri)

    try:
        s3_client.download_file(bucket_name, key, local_file_path)
        print("File downloaded successfully.")
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print("The object does not exist.")
        else:
            print("An error occurred while downloading the file.")


def parse_s3_uri(s3_uri):
    # Remove the "s3://" prefix and split the remaining string into bucket name and key
    s3_uri = s3_uri.replace("s3://", "")
    parts = s3_uri.split("/")
    bucket_name = parts[0]
    folder = "/".join(parts[1:-1])
    key = parts[-1]

    return bucket_name, folder, key


def download_file(url, local_file_path, reporthook):
    if is_s3_url(url):
        # download from s3
        # bucket_name, folder, key = parse_s3_uri(url)
        # s3_handler = DATABASE_IDS.handlers().get(DATABASE_IDS.AWS)
        # s3_handler = s3_handler(bucket_name, folder)
        s3_client = boto3.client("s3")
        bucket_name, folder, key = parse_s3_uri(url)
        try:
            s3_client.download_file(bucket_name, f"{folder}/{key}", local_file_path)
            print("File downloaded successfully.")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                print("The object does not exist.")
            else:
                print("An error occurred while downloading the file.")

    elif url_exists(url):
        try:
            urllib.urlretrieve(url, local_file_path, reporthook=reporthook)
        except Exception as e:
            log.error(f"error fetching file {e}, {url}")
    else:
        raise Exception(f"Url does not exist {url}")


# def is_full_url(file_path):
#     return file_path.find("http") != -1 or file_path.find("ftp") != -1


def is_full_url(file_path):
    url_regex = re.compile(
        r"^(?:http|https|ftp|s3)://", re.IGNORECASE
    )  # check http, https, ftp, s3
    return re.match(url_regex, file_path) is not None


def is_s3_url(file_path):
    return file_path.find("s3://") != -1


def is_remote_path(file_path):
    """
    @param file_path: str
    """
    for ele in DATABASE_IDS.with_colon():
        if ele in file_path:
            return True


def convert_db_shortname_to_url(file_location):
    """
    @param file_path: str
    """
    database_name, file_path = file_location.split(":")
    database_url = REPLACE_PATH[f"{database_name}:"]
    if database_url is not None:
        return database_name, f"{database_url}/{file_path}"
    return database_name, file_path


def get_cache_location(name, cache, destination):
    """
    name: str
    destination: str
    """
    local_file_directory = CACHE_DIR[cache] / destination
    local_file_path = local_file_directory / name
    make_directory_if_needed(local_file_directory)
    return local_file_path


def get_local_file_location(
    input_file_location, destination="", cache="geometries", force=False
):
    """
    Options:
    1. Find file locally, return the file path
    2. Download file to local cache, return path (might involve replacing short-code in url)
    3. Force download even though you have a local copy

    Returns location of file (either already there or newly downloaded)
    """
    if is_remote_path(input_file_location):
        database_name, file_path = convert_db_shortname_to_url(input_file_location)
        if database_name == "firebase":
            pass
        else:
            input_file_location = file_path
    if is_full_url(input_file_location):
        url = input_file_location
        reporthook = None
        if helper is not None:
            reporthook = helper.reporthook

        name = url.split("/")[-1]  # the recipe name
        local_file_path = get_cache_location(name, cache, destination)
        # check if the file is already downloaded
        # if not, OR force==True, download file
        if not os.path.isfile(local_file_path) or force:
            download_file(url, local_file_path, reporthook)
        log.info(f"autopack downloaded and stored file: {local_file_path}")
        return local_file_path

    # not url, use pathlib
    input_file_location = Path(input_file_location)
    if os.path.isfile(CACHE_DIR[cache] / input_file_location):
        return CACHE_DIR[cache] / input_file_location
    if os.path.isfile(CURRENT_RECIPE_PATH / input_file_location):
        # if no folder provided, use the current_recipe_folder
        return CURRENT_RECIPE_PATH / input_file_location

    # didn't find the file locally, finally check db
    url = autoPACKserver + "/" + str(cache) + "/" + str(input_file_location)
    if url_exists(url):
        reporthook = None
        if helper is not None:
            reporthook = helper.reporthook
        name = input_file_location
        local_file_path = CACHE_DIR[cache] / destination / name
        download_file(url, local_file_path, reporthook)
        return local_file_path
    return input_file_location


def read_text_file(filename, destination="", cache="collisionTrees", force=None):
    if is_remote_path(filename):
        database_name, file_path = convert_db_shortname_to_url(filename)
        if database_name == "firebase":
            # TODO: read from firebase
            # return data
            pass
        else:
            local_file_path = get_local_file_location(
                file_path, destination=destination, cache=cache, force=force
            )
    else:
        local_file_path = get_local_file_location(
            filename, destination=destination, cache=cache, force=force
        )
    f = open(local_file_path)
    sphere_data = f.readlines()
    f.close()
    return sphere_data


def load_file(filename, destination="", cache="geometries", force=None):
    if is_remote_path(filename):
        database_name, file_path = convert_db_shortname_to_url(filename)
        # command example: `pack -r firebase:recipes/[FIREBASE-RECIPE-ID] -c [CONFIG-FILE-PATH]`
        if database_name == "firebase":
            db = DATABASE_IDS.handlers().get(database_name)
            initialize_db = db()
            db_handler = DBRecipeLoader(initialize_db)
            recipe_id = file_path.split("/")[-1]
            db_doc, _ = db_handler.collect_docs_by_id(
                collection="recipes", id=recipe_id
            )
            downloaded_recipe_data = db_handler.prep_db_doc_for_download(db_doc)
            return downloaded_recipe_data, database_name
        else:
            local_file_path = get_local_file_location(
                file_path, destination=destination, cache=cache, force=force
            )
    else:
        local_file_path = get_local_file_location(
            filename, destination=destination, cache=cache, force=force
        )
    return json.load(open(local_file_path, "r")), None


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
    load_file(list_of_available_recipes)


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
    for k in CACHE_DIR:
        try:
            shutil.rmtree(CACHE_DIR[k])
            os.makedirs(CACHE_DIR[k])
        except:  # noqa: E722
            print("problem cleaning ", CACHE_DIR[k])


def write_username_to_creds():
    username = getpass.getuser()
    creds = read_json_file("./.creds")
    if creds is None or "username" not in creds:
        creds = {}
        creds["username"] = username
        write_json_file("./.creds", creds)


# we should read a file to fill the RECIPE Dictionary
# so we can add some and write/save setup
# afdir  or user_pref
if checkAtstartup:
    checkPath()
    # updatePathJSON()
    # checkRecipeAvailable()
    log.info("path are updated ")

# write username to creds
write_username_to_creds()

log.info(f"currently number recipes is {len(RECIPES)}")
# check cache directory create if doesnt exit.abs//should be in user pref?
# ?
# need a distinction between autopackdir and cachdir
wkr = afdir
# in the predefined working directory

BD_BOX_PATH = "/home/ludo/Tools/bd_box-2.2"  # or /Users/ludo/DEV/bd_box-2.1/
GMODE = "Simple"
