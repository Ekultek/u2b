#!/usr/bin/env python

from lib.settings import search_for_iso, avail_drives, unzip_iso, download_iso

#print avail_drives()
#print search_for_iso()
#unzip_iso("dsl-4.11.rc1.iso")
print download_iso("pentest", "parrot", verbose=True)