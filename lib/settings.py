# ~*~ encoding: utf-8 ~*~

import os
import itertools
import time
import math
import sys
import json
import datetime
import multiprocessing

import psutil
import requests

import lib

from download_iso import (
    start_stream_download,
    NoLinkFoundException,
    DownloadedEmptyException
)

CLONE_LINK = "https://github.com/ekultek/i2b.git"
TYPE_COLORS = {"dev": 33, "stable": 92}
VERSION = "1.0"

if len(VERSION) >= 4:
    VERSION_STRING = "\033[92mv{}\033[0m(\033[{}m\033[1m#dev\033[0m)".format(VERSION, TYPE_COLORS["dev"])
else:
    VERSION_STRING = "\033[92mv{}\033[0m(\033[{}m\033[1m*stable\033[0m)".format(VERSION, TYPE_COLORS["stable"])

BANNER = ("""\033[36m     
        .-''-.               
.--.  .' .-.  )   /|     -> iso2bootable   
|__| / .'  / /    ||     -> {} 
.--.(_/   / /     ||     -> {}\033[36m     
|  |     / /      ||  __     
|  |    / /       ||/'__ '.  
|  |   . '        |:/`  '. ' 
|  |  / /    _.-')||     | | 
|__|.' '  _.'.-'' ||\    / ' 
   /  /.-'_.'     |/\\'..' /  
  /    _.'        '  `'-'`   
 ( _.-'                      
{}\033[0m""".format(CLONE_LINK, VERSION_STRING, "=" * 30))


def create_dir(dirname, verbose=False):
    """
      Create a directory if it does not exist
    """
    if not os.path.exists(dirname):
        if verbose:
            lib.log.console_log.LOGGER.debug("Directory '{}/*' not found, creating it..".format(dirname))
        os.mkdir(dirname)
    else:
        lib.log.console_log.LOGGER.debug("Directory '{}/*' found, skipping..".format(dirname))


def avail_drives(verbose=False):
    def _find_path(data, verbose=False):
        if verbose: lib.log.console_log.LOGGER.debug("Finding path index..")
        start_index = data.find("/")
        if verbose: lib.log.console_log.LOGGER.debug("Index found: '{}'. Path is: '{}'..".format(start_index, data[start_index:-1]))
        return data[start_index:-1]

    def _get_drive_size(path, verbose=False):
        if verbose: lib.log.console_log.LOGGER.debug("Calculating size of drive..")
        vfs = os.statvfs(path)
        available = vfs.f_frsize * vfs.f_blocks
        if verbose: LOGGER.debug("Drive size is equal to: '{}' ({} bytes)..".format(
            convert_file_size(available), available)
        )
        return available

    usable_boots = set()
    data_disks = psutil.disk_partitions()
    for disk in data_disks:
        if "/media" in disk[1]:
            usable_boots.add(disk)
    if usable_boots:
        if verbose: lib.log.console_log.LOGGER.debug("Found usable drive(s): '{}'..".format(usable_boots))
        path_data = _find_path(str(usable_boots).split(",")[0], verbose=verbose)

        return {
            "path": path_data,
            "size": _get_drive_size(path_data, verbose=verbose)
        }
    else:
        lib.log.console_log.LOGGER.debug(
            "It seems that you either do not have a USB in the system, "
            "or have your system setup in a way not recognized by i2B. "
            "Please check your USB's and your system configuration and "
            "try again. Exiting.."
        )
        return None


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
            lib.log.console_log.LOGGER.debug("Starting {} processes to search directory '{}' for .iso files..".format(
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
                    lib.log.console_log.LOGGER.debug("Found .iso file: '{}'".format(data))
                retval.add(data)
    else:
        if verbose:
            lib.log.console_log.LOGGER.debug("Searching {} for .iso files..".format(dirname))
        for iso in os.listdir(dirname):
            if iso.endswith(".iso"):
                if verbose:
                    lib.log.console_log.LOGGER.debug("Found {}..".format(iso))
                retval.add(iso)
    if len(retval) == 0:
        lib.log.console_log.LOGGER.debug("No ISO files found. Verify directory and try again.")
    return list(retval)


def convert_file_size(byte_size, magic_num=1024):
    """
      Convert a integer to a file size (B, KB, MB, etc..)
      > :param byte_size: integer that is the amount of data in bytes
      > :param magic_num: the magic number that makes everything work, 1024
      > :return: the amount of data in bytes, kilobytes, megabytes, etc..
    """
    byte_size = float(byte_size)
    if byte_size == 0:
        return "0B"
    # Probably won't need more then GB, but still it's good to have
    size_data_names = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    floored = int(math.floor(math.log(byte_size, magic_num)))
    pow_data = math.pow(magic_num, floored)
    rounded_data = round(byte_size / pow_data, 2)
    return "{}{}".format(rounded_data, size_data_names[floored])


def download(iso_type, distro, verbose=False, json_path="{}/lib/data_files/iso_data.json", personal=None):
    def get_filename(link):
        return link.split("/")[-1]

    is_64bit = sys.maxsize > 2 ** 32
    arch = "64" if is_64bit else "32"
    if verbose:
        lib.log.console_log.LOGGER.debug("Platform architecture appears to be {}bit...".format(arch))
    json_info = open(json_path.format(os.getcwd())).read()
    json_resp = json.loads(json_info)
    json_data = json_resp["iso_links"]
    if personal is None:
        try:
            download_link = json_data[iso_type][distro][arch]
            if verbose:
                lib.log.console_log.LOGGER.debug("Fetching download link..")
                if download_link is not None:
                    lib.log.console_log.LOGGER.debug("Found: '{}'".format(download_link))
        except Exception:
            raise NoLinkFoundException(
                "It appears that you have not entered a valid link, try again.. "
                "With the ISO link flag (--iso-link=<LINK>)."
            )
    else:
        download_link = personal
    filename = get_filename(download_link)
    resp = requests.get(download_link, stream=True)
    if verbose:
        lib.log.console_log.LOGGER.debug("Status '{}' '{}' code returned".format(
            "OK" if resp.status_code == 200 else "FAILED",
            resp.status_code
        ))
    if resp.status_code != 200:
        raise NoLinkFoundException(
            "The website returned a status code of '{}'. "
            "It seems that the link is broken, double check "
            "the link or pass your own with the ISO link flag "
            "(--iso-link=<LINK>). If you grabbed the print link from "
            "the JSON file, make an issue about this".format(resp.status_code)
        )
    download_total = resp.headers.get("content-length")
    if download_total is None:
        DownloadedEmptyException(
            "The ISO link '{}' returned an empty content-length "
            "header. This could mean it was moved or deprecated. "
            "Find the appropriate ISO download link and try again "
            "with the ISO link flag (--iso-link=<LINK>)."
        )
    else:
        start_time = time.time()
        if verbose:
            lib.log.console_log.LOGGER.debug("Downloading a total of {}..".format(convert_file_size(float(download_total))))

        start_stream_download(filename, resp)
        stop_time = time.time() - start_time
        lib.log.console_log.LOGGER.debug("Done, time elapsed since download started: {}. Saved as: {}..".format(stop_time, filename))


def mount_drive(path):
    import glob
    for root, sub, f in os.walk(path):
        print root, sub, f


def create_autorun(label, directory, filename="autorun.inf"):
    autorun_data = "; Created by i2B (iso to boot) {}\n"
    autorun_data += "; https://github.com/ekultek/i2B\n"
    autorun_data += "[autorun]\n"
    autorun_data += "icon = radiation.ico\n"
    autorun_data += "label = {}"
    with open(directory + "/" + filename, "a+") as auto:
        auto.write(autorun_data.format(datetime.datetime.today(), label))
