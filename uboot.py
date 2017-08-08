#!/usr/bin/env python

import os

from var.extract import unzip_iso
from var.format.formatter import Formatter

from lib.settings import (
    search_for_iso,
    avail_drives,
    download,
    mount_drive,
    create_autorun,
    BANNER,
    create_dir
)

print BANNER

create_dir("log")

# print avail_drives(verbose=True)
# Formatter("/dev/sdb1").format_usb(4096)
# print search_for_iso(verbose=True)
# unzip_iso("dsl-4.11.rc1.iso", label="TEST", verbose=True)
print download("pentest", "kali", verbose=True)
# mount_drive("/media/baal/ARCH_201707")
# create_autorun("test", directory=os.getcwd())
