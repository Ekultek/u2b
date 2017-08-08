import subprocess
import string
import os
import random

from lib.settings import (
    create_dir,
    create_autorun
)
from lib.log import (
    console_log,
)


# if you can fix this shit, please do because I hate this function
# it's the only way I could get this damn thing to work though..
def unzip_iso(filepath, label=None, verbose=False, directory_name="ISO_dir"):
    """
      Unzip the ISO file into a directory using the file-roller command
    """

    def create_rand_dir_name(chars=string.ascii_letters, verbose=False):
        """
          Create a random directory name
        """
        if verbose: console_log.LOGGER.debug("Creating random directory name..")
        retval = set()
        for _ in range(8):
            retval.add(random.choice(chars))
        return ''.join(list(retval))

    dir_name = create_rand_dir_name(verbose=verbose)
    if verbose: console_log.LOGGER.debug("Creating directory: {}/{}/*..".format(directory_name, dir_name))
    create_dir(directory_name)
    create_dir(directory_name + "/" + dir_name, verbose=verbose)
    full_dir_path = os.getcwd() + "/" + directory_name + "/" + dir_name
    if verbose: console_log.LOGGER.debug("Directory created, full path being saved to: {}..".format(full_dir_path))

    # Create the file roller command, this will eventually be replaced, but
    # we're gonna go ahead and use it for now. At least until I can figure out
    # what the fuck I'm doing when it comes to ISO9660 or hachoir parsers.
    # Have you ever tried using those fucking things? It's damn near impossible
    # there is ZERO documentation on it, and about 234982349028 fucking files with it
    # like WTF?! Why even create it just to have people guess how it works?!
    # So guess what hachoir?! FUCK YOU and ISO9660, fuck you too! ** END RANT **
    cmd = "file-roller -e {} {} 2> /dev/null".format(full_dir_path, filepath)
    if verbose: console_log.LOGGER.debug("Starting command: {} ..".format(cmd))
    stdout_data = subprocess.check_call(cmd, shell=True)
    if stdout_data == 0:
        if verbose: console_log.LOGGER.debug("Command completed successfully..")
        if label is None:
            label_name = [c for c in os.listdir(full_dir_path) if c.isupper()]
        else:
            label_name = label
        create_autorun(''.join(label_name) if type(label_name) == list else label_name, full_dir_path)
        return True
    else:
        if verbose: console_log.LOGGER.debug("Command failed with code: {}".format(stdout_data))
        return False
