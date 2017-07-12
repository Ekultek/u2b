import os
import logging
import itertools
import time
import math
import sys
import json
import shutil
import multiprocessing

import psutil
import requests
from colorlog import ColoredFormatter

from thirdparty.iso9660 import ISO9660

log_level = logging.DEBUG
logger_format = "[%(log_color)s%(asctime)s %(levelname)s%(reset)s] %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(log_level)
formatter = ColoredFormatter(logger_format, datefmt="%H:%M:%S",
                             log_colors={
                                 "DEBUG": "bold,cyan",
                                 "INFO": "green",
                                 "WARNING": "yellow",
                                 "ERROR": "red",
                                 "CRITICAL": "bold,red"
                             })
stream = logging.StreamHandler()
stream.setLevel(log_level)
stream.setFormatter(formatter)
LOGGER = logging.getLogger('configlog')
LOGGER.setLevel(log_level)
LOGGER.addHandler(stream)


def create_dir(dirname, verbose=False):
    """
      Create a directory if it does not exist
    """
    if not os.path.exists(dirname):
        if verbose:
            LOGGER.debug("Directory '{}/*' not found, creating it..".format(dirname))
        os.mkdir(dirname)
    else:
        LOGGER.debug("Directory found, skipping..")


def avail_drives(verbose=False):
    usable_boots = set()
    data_disks = psutil.disk_partitions()
    for disk in data_disks:
        if verbose:
            LOGGER.debug("Found {}..".format(disk))
        if "/media" in disk[1]:
            usable_boots.add(disk)
    return list(usable_boots)


def prompt(reason, data):
    return raw_input("[{} PROMPT] {}[{}]: ".format(time.strftime("%H:%M:%S"), reason, data))


def worker(filename):
    """
      The worker for multiprocessing the directory search
    :param filename: Filename to be tested to see if it contains the ISO
      extension or not, if it does not contain the extension nothing
      important will happen
    :return: The filename if it contains the .iso eextension
    """
    if filename.endswith(".iso"):
        return filename


def search_for_iso(dirname=None, proc_num=48, verbose=False, default_path="/"):
    """
      Find all ISO files associated with the directory given, if no directory is given
      we're gonna go ahead and search through the root directory to find them. If multiple
      ISO files are found it will prompt you for which file you want to use.

    :param dirname: Directory to be searched through. When no directory is given as
      an argument to the 'dirname' variable, it will do a multiprocess search through
      the root directory (default_path) and search for all files ending in .iso extension.
    :param proc_num: The number of processes to be run while searching through the root
      directory as the default search. If no number is specified it will default to 48
      processes running. This will not give much of a speed up due to the CPU being faster
      then the hardware, but it will speed it up a little bit.
    :param verbose: Verbosity to be ran, default is False so it won't really output much.
      If the variable is changed to True it will output more information about what's going
      on behind the scenes.
    :param default_path: The default path that will be searched through if no directory is
      given to the 'dirname' variable.
    :return: A directory path containing an ISO file to be used.
    """
    retval = set()
    if dirname is None:
        if verbose:
            LOGGER.debug("Starting {} processes to search  directory '{}' for .iso files..".format(
                proc_num, default_path
            ))
            # start multiprocessing the search using the number of given processes
        pool = multiprocessing.Pool(processes=proc_num)
        walker = os.walk(default_path)
        file_data_gen = itertools.chain.from_iterable(
            (os.path.join(root, f) for f in files)
            for root, sub, files in walker
        )
        results = pool.map(worker, file_data_gen)
        for data in results:
            if data is not None:
                if verbose:
                    LOGGER.debug("Found .iso file: '{}'".format(data))
                retval.add(data)
    else:
        if verbose:
            LOGGER.debug("Searching {} for .iso files..".format(dirname))
        for iso in os.listdir(dirname):
            if iso.endswith(".iso"):
                if verbose:
                    LOGGER.debug("Found {}..".format(iso))
                retval.add(iso)
    if len(retval) == 0:
        LOGGER.fatal("No ISO files found. Verify directory and try again.")
    return list(retval)


def unzip_iso(filepath, verbose=False):
    iso_file = ISO9660(filepath)

    def create_dirname(path):
        data = path.split("/")[-1]
        items = data.split(".")
        return items[0]

    for iso_item in iso_file.tree():
        if iso_item == "/":
            pass
        else:
            shutil.copyfile(iso_item, create_dirname(filepath))


def convert_file_size(byte_size, magic_num=1024):
    """
      Convert a integer to a file size (B, KB, MB, etc..)
      > :param byte_size: integer that is the amount of data in bytes
      > :param magic_num: the magic number that makes everything work, 1024
      > :return: the amount of data in bytes, kilobytes, megabytes, etc..
    """
    if byte_size == 0:
        return "0B"
    # Probably won't need more then GB, but still it's good to have
    size_data_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    floored = int(math.floor(math.log(byte_size, magic_num)))
    pow_data = math.pow(magic_num, floored)
    rounded_data = round(byte_size / pow_data, 2)
    return "{}{}".format(rounded_data, size_data_names[floored])


def download_iso(iso_type, distro, verbose=False, json_path="{}/lib/data_files/iso_data.json"):
    def get_filename(link):
        return link.split("/")[-1]

    is_64bit = sys.maxsize > 2 ** 32
    arch = "64" if is_64bit else "32"
    if verbose:
        LOGGER.debug("Platform architecture appears to be {}bit...".format(arch))
    json_info = open(json_path.format(os.getcwd())).read()
    json_resp = json.loads(json_info)
    json_data = json_resp["iso_links"]
    download_link = json_data[iso_type][distro][arch]
    filename = get_filename(download_link)
    resp = requests.get(download_link, stream=True)
    download_total = resp.headers.get("content-length")
    with open(filename, "a+") as iso_file:
        if download_total is None:
            iso_file.write(resp.content)
            LOGGER.critical(
                "File was saved empty, either the link is broken '{}' "
                "or something bad happened..."
            )
            # TODO:\ Create a option to download 32bit
        else:
            # TODO:\ Finish the download stream
            pass

