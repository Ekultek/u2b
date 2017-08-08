import sys
import time

import lib


class NoLinkFoundException(Exception):
    pass


class DownloadedEmptyException(Exception):
    pass


def start_stream_download(filename, stream):
    lib.log.console_log.LOGGER.warning("This will take awhile, please be patient..")
    with open(filename, "a+") as data_stream:
        for i, data in enumerate(stream.iter_content(chunk_size=2048)):
            data_stream.write(data)
            while data:
                sys.stdout.write(".")
                time.sleep(1)
                sys.stdout.flush()
        print("")
