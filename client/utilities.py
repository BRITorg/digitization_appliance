"""A collection of functions supporting image processing workflows."""

import platform
import os
import datetime
import re
import sys
import logging
from hashlib import md5
from PIL import Image
from pyzbar.pyzbar import decode

UTILITIES_LOGGER = logging.getLogger('session_log')


def barcodes(file_path=None):
    """
    Extract all barcode values and symbology types from an image file.

    Paramaters
    ----------
    file_path : string


    Returns
    -------
    list
        A list of dicts with the barcode type (symbology)
        and data (barcode value).

    """
    try:
        barcodes = decode(Image.open(file_path))
        barcodes_list = []
        if barcodes:
            # reformat into a list
            for barcode in barcodes:
                symbology_type = str(barcode.type)
                data = barcode.data.decode('UTF-8')
                barcodes_list.append({'type': symbology_type, 'data': data})
        else:
            UTILITIES_LOGGER.info('No barcodes found in file: ' + file_path)
            return None
        return barcodes_list
    except OSError as e:
        print('ERROR: unable to read file. errno: ' + str(e.errno) + ' filename: ' + str(e.filename) + ' strerror: ' + str(e.strerror))
        UTILITIES_LOGGER.exception('OSError')
        return None


def sort_barcodes(barcode_list):
    """
    Sort a barcode list in a 'more intuitive' way.

    Using the alphanum_key function, sorts letters alphabeticaly
    and number chunks as their full numerical value.
    Inspired by https://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return sorted(barcode_list, key=alphanum_key)


def alphanum_key(s):
    """
    Turn a string into a list of string and number chunks.

    "z23a" -> ["z", 23, "a"]
    From https://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [int(c) if c.isdigit() else c for c in re.split('([0-9]+)', s)]


def md5hash(file_path=None):
    """
    Generate a md5 checksum of a file.

    This approach ensures larger files can be read into memory.

    From https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
    """
    if file_path is not None:
        hash_md5 = md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except PermissionError as e:
            print('ERROR: PermissionError - unable to read file: ' + file_path)
            # TODO consider suppressing multiple errors using logging filter https://stackoverflow.com/a/44692178/560798
            UTILITIES_LOGGER.error('PermissionError - Unable to read file. Errno: ' + str(e.errno) + ' filename: ' + str(e.filename) + ' strerror: ' + str(e.strerror))
            return None
    else:
        UTILITIES_LOGGER.info('No path provided, can not generate MD5 hash.')
        return None


def creation_date(file_path):
    """
    Determine file creation date across different OS and file platforms.

    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.

    From https://stackoverflow.com/a/

    Notes
    Perhaps just use https://docs.python.org/3/library/os.path.html#os.path.getmtime instead?
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    date = None
    if platform.system() == 'Windows':
        try:
            date = os.path.getctime(file_path)
        except FileNotFoundError:
            print('FileNotFoundError: ' + file_path)
            UTILITIES_LOGGER.error('FileNotFoundError: ' + file_path)
    else:
        try:
            stat = os.stat(file_path)
            try:
                date = stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                date = stat.st_mtime
        except FileNotFoundError as e:
            print('FileNotFoundError: ' + file_path)
            UTILITIES_LOGGER.exception('FileNotFoundError: ' + file_path)
    # return datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d %H:%M:%S')
    # Got error: OverflowError: timestamp out of range for platform time_t
    # When manually testing with existing files from Windows. Probably not an issue in real
    # usage, but fixed anyway with datetime.datetime.utcfromtimestamp().
    # See: https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date#comment30046351_3682808
    try:
        return datetime.datetime.utcfromtimestamp(int(date)).strftime('%Y-%m-%d %H:%M:%S')
    except OverflowError as e:
        # Getting OverflowError when testing with some files, not sure of root cause
        # This perhaps is only a problem when the file is read on creation when copied to sesison directory.
        # It gets read a second time when modified. Need to wait for the copy to finish?
        print('OverflowError: date value: ' + str(date) + ' for file:' + file_path)
        UTILITIES_LOGGER.exception('OverflowError: date:' + str(date) + ' file:' + file_path)
        return None


def rename_uniquely(image_path=None, catalog_number=None, image_event_id=None):
    """
    Generate a unique file path to rename files based on the catalog number.

    Rename a file in place using the catalog number. If the desired filename exists,
    the image event UUID is appended.
    """
    if image_path is not None:
        # Construct desired path
        image_directory, original_image_basename = os.path.split(image_path)
        image_file_name, image_extension = os.path.splitext(original_image_basename)
        new_image_path = os.path.join(image_directory, catalog_number + image_extension)
        # Determine if desired path is unique
        if os.path.exists(new_image_path):
            # path_is_unique = False
            # construct alternative path
            new_image_path = os.path.join(image_directory, catalog_number + '_' + image_event_id + image_extension)
            if os.path.exists(new_image_path):
                path_is_unique = False
            else:
                path_is_unique = True
        else:
            path_is_unique = True
    else:
        # new_image_path = None
        UTILITIES_LOGGER.error('No image path provided')
        return None

    # Check if path is unique
    if path_is_unique:
        try:
            os.rename(image_path, new_image_path)
            UTILITIES_LOGGER.info('Renaming - source:' + image_path + ' destination: ' + new_image_path)
            return new_image_path
        except OSError:
            # Possible problem with character in new filename
            print('ALERT - OSError. new path:', new_image_path)
            UTILITIES_LOGGER.exception('OSError - unspecified problem with path: ' + new_image_path)
            return None
        except:
            print("Unexpected error:", sys.exc_info()[0])
            UTILITIES_LOGGER.exception('Unexpected error for path: ' + new_image_path + ' ' + sys.exc_info()[0])
            raise
    else:
        print('Image path is not unique:', new_image_path)
        UTILITIES_LOGGER.error('Image path not unique: ' + new_image_path)
        return None
