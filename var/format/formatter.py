import io
import lib


class CancelBlockCipherException(Exception): pass


class Formatter(object):

    def __init__(self, usb):
        self.usb = usb

    def _erase_all(self, block_cipher):
        with io.FileIO(self.usb, "w") as _usb:
            while _usb.write(block_cipher): print _usb

    def format_usb(self, size, default="y"):
        block_cipher = b"\0" * size
        confirmation = lib.settings.prompt(
            "Your USB is about to be completely erased, everything on this "
            "drive will be gone, are you sure you want to continue", "y/N(default '{}')".format(default)
        )
        if confirmation.lower().startswith("y") or confirmation == "":
            lib.settings.LOGGER.warning("Erasing USB content..")
            self._erase_all(block_cipher)
        elif confirmation.lower() == "" or confirmation is None:
            lib.settings.LOGGER.warning("Erasing USB content..")
            self._erase_all(block_cipher)
        else:
            raise CancelBlockCipherException("User aborted block cipher.")


class UDF(Formatter):

    def __init__(self, usb):
        super(UDF, self).__init__(usb)


class FAT32(Formatter):

    def __init__(self, usb):
        super(FAT32, self).__init__(usb)


class NTFS(Formatter):

    def __init__(self, usb):
        super(NTFS, self).__init__(usb)


class exFAT(Formatter):

    def __init__(self, usb):
        super(exFAT, self).__init__(usb)


class Fat(Formatter):

    def __init__(self, usb):
        super(Fat, self).__init__(usb)