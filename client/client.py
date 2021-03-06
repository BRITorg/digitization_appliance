# from argparse import ArgumentParser
import atexit
import configparser
import datetime
import json
import logging
import os
import re
import time
import uuid

import utilities
import blur_detection

import click
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

RAW_IMAGE_PATTERNS = ['*.cr2', '*.CR2']  # use later to detect original creation of raw files
DERIVED_IMAGE_PATTERNS = ['*.jpg', '*.JPG']
IMAGE_PATTERNS = RAW_IMAGE_PATTERNS + DERIVED_IMAGE_PATTERNS
valid_catalog_number_patterns = ['BRIT\d+$', 'NLU\d+$', 'ANHC\d+$', 'UARK\d+$', '\d+$']
REQUIRED_CATALOG_NUMBER_PREFIX = ''  # This will be prepended to the selected catalog_number if it doesn't exist
SESSION_LOGGER = logging.getLogger('session_log')
config_local_path = 'config_local.ini'
# config_path = 'config.ini'


class Client():
    """
    Client is the first core object created when the application runs.

    Gathers configuration parameters.


    """

    global SESSION_LOGGER

    def __init__(self, client_ui=None):
        """Initialize client values."""
        # Load config_local
        config_local = configparser.ConfigParser(allow_no_value=True)
        config_local.read(config_local_path)
        try:
            station_uuid = config_local.get('LOCAL','station_uuid')
            station_id = config_local.get('LOCAL','station_id')
            SESSION_LOGGER.info('Client loaded configuration:', config_local_path)
        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            print('Can not read options', e)
            station_uuid = None
            station_id = None
        self.station_uuid = station_uuid
        self.station_id = station_id
        # Client can only have one active session at at time.
        self.session = None
        self.client_ui = client_ui

        # Set up logging
        print('Setting up logging.')
        if self.station_uuid:
            log_filename = self.station_id + '_' + self.station_uuid + '.log'
        else:
            log_filename = 'UNIDENTIFIED_STATION.log'
        log_path = log_filename
        SESSION_LOGGER.setLevel(logging.DEBUG)
        session_handler = logging.FileHandler(log_path)
        session_handler.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        session_handler.setFormatter(log_formatter)
        SESSION_LOGGER.addHandler(session_handler)
        SESSION_LOGGER.info('Client loaded.')

class Session():
    global SESSION_LOGGER
    def __init__(self, path=None, client_instance=None, client_ui=None):
        self.uuid = str(uuid.uuid4())
        self.path = path
        self.project_code = None
        self.collection_code = None
        self.username = None
        self.image_events = []
        self.start_time = None
        self.notes = None
        self.taxa = None
        # TODO move client_ui to Client class
        # make it work with both CLI and GUI
        self.client_ui = client_ui
        self.client_instance = client_instance
        if self.client_instance:
            print('client_instance:')
            print(self.client_instance.station_uuid)
            print(self.client_instance.station_id)
        else:
            print('No client_instance.')
        print('client.Session: Session initialized.')

    def start(self):
        """When called from the PYQT GUI, start is executed in a QThread"""

        if self.path:
            # TODO make sure path is valid and writable
            self.start_time = datetime.datetime.now()
            print('Started monitoring of:', self.path, self.start_time)
            # start watching session folder for file additions and changes
            event_handler = ImageHandler(session=self, patterns=IMAGE_PATTERNS)
            # event_handler = ImageHandler(patterns=IMAGE_PATTERNS)
            observer = Observer()
            observer.schedule(event_handler, self.path, recursive=True)
            observer.start()
            SESSION_LOGGER.info('Session monitor started.')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print('Ending by KeyboardInterrupt')
            observer.join()
        else:
            print('No path to monitor.')

    def elapsed_time(self):
        """Return the time elapsed since the session was started."""
        if self.start_time:
            return datetime.datetime.now() - self.start_time
        else:
            return None

    def imaging_rate(self):
        """Return the rate of images created per minute."""
        session_duration = self.elapsed_time()
        image_count = len(self.image_events)
        if image_count > 0:
            if session_duration:
                session_duration_minutes = session_duration.total_seconds() / 60
                return image_count / session_duration_minutes
            else:
                return None
        else:
            return None

    def register_image_event(self, image_path=None):
        """
        Create an image event or add image file to existing event.

        Determine if the image_path representing an image event has been registered.
        If the image_path has been resistered (exists in self.image_events) then the
        existing image event is updated.
        If the image event has not been registered, a new image event is created
        then registered in self.image_events.

        Parameters
        ----------
        image_path: string

        Returns
        -------
        ImageEvent
        """
        if image_path is not None:
            # search for existing image event with matching image filename
            basename = os.path.basename(image_path)
            filename, file_extension = os.path.splitext(basename)
            # Check if the event has already been registered by comparing the filename
            existing_event = self.matching_image_event(filename)
            if existing_event:
                # Add file info to existing event
                # TODO use file pattern vars
                if file_extension.upper() == '.CR2':
                    existing_event.original_raw_image = image_path
                    print('Added CR2 to existing image event: ' + basename)
                    SESSION_LOGGER.info('Added CR2 to existing event: ' + existing_event.id)
                    # existing_event.populate_raw_metadata()
                    # existing_event.serialize_image_event()
                elif file_extension.upper() == '.JPG':
                    existing_event.original_derived_image = image_path
                    print('Added JPG to existing image event: ' + basename)
                    SESSION_LOGGER.info('Added JPG to existing event: ' + existing_event.id)
                    #existing_event.populate_derived_metadata()
                    #existing_event.serialize_image_event()
                else:
                    print('ERROR: no matching file extension to augment existing image event.')
                    SESSION_LOGGER.error('No matching file extension to augment existing image event: ' + existing_event.id)
                # TODO save any updates to event JSON file
                # Instead of above steps, trying just update_image_event to consolidate code.
                # This will populate file metadata for each
                existing_event.update_image_event(original_image_path=image_path)
                return existing_event
            # Matching event has not been registered
            # Create a new event
            else:
                new_image_event = ImageEvent(session=self, original_image_path=image_path)
                print('Creating new image event based on : ' + basename)
                SESSION_LOGGER.info('Created new image event: ' + new_image_event.id + ' based on file: ' + basename)
                # Add image_event to session
                self.image_events.append(new_image_event)
                # Add image event to client GUI
                if self.client_ui:
                    self.client_ui.add_event(event=new_image_event)
                return new_image_event

    def matching_image_event(self, filename=None):
        for image_event in self.image_events:
            if image_event.original_filename == filename:
                return image_event
        return None

    def end_session(self):
        # TODO try registering cleanup for session variable so it happens after end_session
        print('Session monitoring ended')
        # TODO serialize session data
        print('Session username: {}'.format(self.username))
        print('Session ID: {}'.format(self.uuid))
        print('Session path: {}'.format(self.path))
        # print('Image event IDs:')
        for event in self.image_events:
            print(event.id, event.catalog_number)
            event.rename_files()
        #print('Completing final sync...STUB')
        # os.system("rsync -arz " + session['path'] + " /Users/jbest/Desktop/demo_shared")
        SESSION_LOGGER.info('Session monitor terminated.')

class ImageEvent():
    global SESSION_LOGGER
    # TODO
    # consider using properties: https://stackoverflow.com/a/2825580/560798

    def __init__(self, session=None, original_image_path=None):
        if session:
            # self.session = session
            self.session_uuid = session.uuid
            self.session_path = session.path
            self.creator = session.username
            self.collection_code = session.collection_code
            self.project_code = session.project_code
            self.session_notes = session.notes
            self.session_taxa = session.taxa
            # self.station_code = session.station_code
            self.station_uuid = session.client_instance.station_uuid
            self.station_id = session.client_instance.station_id
        else:
            # self.session = None
            self.session_path = None
            self.creator = None
            self.collection_code = None
            self.project_code = None
            self.session_notes = None
            self.session_taxa = None
            # self.station_code = None
            self.station_uuid = None
            self.station_id = None
        # Generate GUID for image event
        self.id = str(uuid.uuid4())
        self.status = ''
        self.status_level = ''
        self.original_raw_image = None
        self.new_raw_image = None
        self.raw_image_creation_date = None
        self.raw_image_md5hash = None
        self.original_derived_image = None
        self.new_derived_image = None
        self.original_filename = None  # Used as key to match raw and derived image file
        self.catalog_number = None
        self.other_catalog_numbers = None
        self.is_blurry = None
        self.blurriness = None
        if original_image_path is not None:
            # update new image event metadata based on image file
            self.update_image_event(original_image_path=original_image_path)
        else:
            print('ERROR: missing original_image_path')

    def evaluate_blurriness(self):
        if self.original_derived_image:
            #TODO file name might be changed before blur is evaluated
            # test both original and new paths?
            try:
                is_blurry, per, blur_extent = blur_detection.blur_detect(self.original_derived_image)
                self.is_blurry = is_blurry
                self.blurriness = blur_extent
                print('evaluate_blurriness:', is_blurry, blur_extent)
            except Exception as e:
                print('evaluate_blurriness: ERROR:', e)
        else:
            print('evaluate_blurriness: no self.original_derived_image')

    def update_image_event_status(self):
        status = ''
        # check if both raw and derived files exist
        if self.original_raw_image and self.original_derived_image:
            status = 'Images complete.'
            self.status_level = 'OK'
            # TODO check if barcode was read
            if self.catalog_number == None:
                status = 'Images complete. No barcode.'
                self.status_level = 'WARNING'
        else:
            if self.original_raw_image:
                status = 'Raw image recorded.'
                self.status_level = 'INFO'
            elif self.original_derived_image:
                status = 'Derived image recorded.'
                self.status_level = 'INFO'
            else:
                status = 'No images recorded.'
                self.status_level = 'ERROR'
        if self.is_blurry == True:
            status = status + ' BLURRY.'
            self.status_level = 'WARNING'

        self.status = status
        print('STATUS:', status)

    def update_image_event(self, original_image_path=None):
        SESSION_LOGGER.info('Updating image event: ' + self.id)
        if original_image_path is not None:
            basename = os.path.basename(original_image_path)
            self.original_filename, file_extension = os.path.splitext(basename)
            if file_extension.upper() == '.CR2':
                self.original_raw_image = original_image_path
                self.populate_raw_metadata()
            elif file_extension.upper() == '.JPG':
                self.original_derived_image = original_image_path
                self.populate_derived_metadata()
            else:
                print('ERROR: no matching file extension to generate image event.')
            self.update_image_event_status()

    def populate_raw_metadata(self):
        if self.original_raw_image is not None:
            self.raw_image_creation_date = utilities.creation_date(file_path=self.original_raw_image)
            self.raw_image_md5hash = utilities.md5hash(file_path=self.original_raw_image)
        else:
            print('ERROR, original_raw_image is None.')

    def populate_derived_metadata(self):
        if self.original_derived_image is not None:
            self.derived_image_md5hash = utilities.md5hash(file_path=self.original_derived_image)
            # Read barcode values and symbologies from derived imaged
            self.barcodes = utilities.barcodes(file_path=self.original_derived_image)
            # Record barcodes for catalog_number and other_catalog_numbers
            barcode_data_list = []
            if self.barcodes:
                for barcode_record in self.barcodes:
                    barcode_data_list.append(barcode_record['data'])
            if len(barcode_data_list) > 0:
                self.catalog_number, self.other_catalog_numbers = derive_catalog_numbers(barcode_data_list)
            else:
                self.catalog_number = None
                self.other_catalog_numbers = None
                #print('WARNING - no barcode found.')
            # evaluate blurriness
            #self.evaluate_blurriness()
        else:
            print('ERROR, original_derived_image is None.')

    def is_minimally_complete(self):
        """ Determines if the image_event is complete enough to serialize. """
        if hasattr(self, 'catalog_number'):
            if len(self.catalog_number) > 0:
                return True
                # if hasattr(self, 'original_raw_image'):
                #    if self.original_raw_image:
                #        return True
        return False

    def serialize_image_event(self):
        """
        Save JSON record
        disabling test for minimal record
        may implement again if needed
        """
        # if self.is_minimally_complete():
        if self.session_path:
            print('serialize_image_event:session_path', self.session_path)
            # TODO - make sure catalog_number can be used in format_filename
            catalog_number_string = self.catalog_number
            if catalog_number_string:
                #json_file_name = catalog_number_string + '_' + self.id + '.JSON'
                json_file_name = catalog_number_string + '.JSON'
            else:
                json_file_name = self.original_filename + '_' + self.id + '.JSON'
            json_path = os.path.join(self.session_path, json_file_name)
            with open(json_path, 'w') as outfile:
                json.dump(self.__dict__, outfile, indent=4)
        else:
            print('No session.path, can not write JSON file.')

    def rename_files(self):
        print(f'rename_files CALLED for {self.id}, {self.catalog_number}')
        # TODO re-create JSON after renaming image files to record new paths
        if self.catalog_number is not None:
            print('Catalog number exists, proceeding...')
            # try:
            # utilities.rename_uniquely(raw_image=self.original_raw_image, \
            #    derived_image=self.original_derived_image, \
            #    catalog_number=self.catalog_number, session_id=self.id)
            if self.original_raw_image is not None:
                new_raw_path = utilities.rename_uniquely(image_path=self.original_raw_image,
                                                         catalog_number=self.catalog_number, image_event_id=self.id)
                print('new_raw_path:', new_raw_path)
                if new_raw_path:
                    self.new_raw_image = new_raw_path
                    self.serialize_image_event()
            else:
                print('No raw image found for catalog number:', self.catalog_number)
            if self.original_derived_image is not None:
                new_derived_path = utilities.rename_uniquely(image_path=self.original_derived_image,
                                                             catalog_number=self.catalog_number, image_event_id=self.id)
                # print('new_derived_path:', new_derived_path)
                if new_derived_path:
                    self.new_derived_image = new_derived_path
                    self.serialize_image_event()
            else:
                print('No derived image found for catalog number:', self.catalog_number)
        else:
            print('Missing catalog number, terminating rename.')


def derive_catalog_numbers(candidates=None):
    """
    This will generate valid catalog numbers based on local protocol
    Returns the canonical catalog number and a list of the other catalog numbers
    all barcodes will be assessed
    any barcodes matching valid_catalog_number_patterns will be further analyzed
    Barcode rules will be applied:
    TODO leading zeros stripped
    prefix prepended
    barcodes sorted
    lowest value selected
    """
    matches = set()
    others = set()
    # Filter out any barcodes which don't match valid_catalog_number_patterns
    for pattern in valid_catalog_number_patterns:
        p = re.compile(pattern)
        # print('Evaluating pattern:', p)
        for candidate in candidates:
            candidate = str(candidate).strip()
            m = p.match(candidate)
            if m:
                matches.add(m.group())
            else:
                others.add(candidate)
    # Standadardize catalog number format
    standardized_catalog_numbers = [REQUIRED_CATALOG_NUMBER_PREFIX+barcode if not barcode.startswith(REQUIRED_CATALOG_NUMBER_PREFIX)
                                    else barcode for barcode in matches]
    # Sort catalog numbers
    sorted_catalog_numbers = utilities.sort_barcodes(standardized_catalog_numbers)
    # Select first catalog number as the canonical identifier
    if len(sorted_catalog_numbers) > 0:
        catalog_number = sorted_catalog_numbers[0]
        # remove catalog number from other catalog numbers
        others.discard(catalog_number)
    else:
        catalog_number = None
    other_catalog_numbers = list(others)
    return catalog_number, other_catalog_numbers


class ImageHandler(PatternMatchingEventHandler):
    global SESSION_LOGGER

    def __init__(self, session=None, patterns=None):
        PatternMatchingEventHandler.__init__(self, patterns=patterns)
        self.session = session

    # Changed to any event
    # Canon app is creating a temp file then renaming
    def on_any_event(self, event):
        image_path = None
        if hasattr(event, 'event_type'):
            event_type = event.event_type
        else:
            event_type = None
        # print('event type:', event_type)
        if hasattr(event, 'src_path'):
            src_path = event.src_path
        else:
            src_path = None
        # print('event src_path:', src_path)
        if hasattr(event, 'dest_path'):
            dest_path = event.dest_path
        else:
            dest_path = None
        # print('event dest_path:', dest_path)
        SESSION_LOGGER.info('File event: ' + str(event_type) + ' src_path: ' + str(src_path) + ' dest_path: ' + str(dest_path))
        # TODO log delete events
        if event_type == 'moved':
            image_path = dest_path
        if event_type == 'modified':
            image_path = src_path
        if event.event_type == 'created':
            # TODO 'created' event_type may only be needed for testing
            image_path = src_path
        if image_path:
            print('image_path:', image_path)
            # image_event = self.session.register_image_event(image_path=image_path)
            self.session.register_image_event(image_path=image_path)
            #self.session.update_image_event_status()
            #self.update_image_event_status()
            SESSION_LOGGER.info('Image file registered: ' + image_path)
        else:
            print('ERROR, no image_path')
            SESSION_LOGGER.error('No image path.')

@click.command()
@click.option('-d', '--directory', help='Specify session directory.')
@click.option('-u', '--username', help='Your first initial and last name')
@click.option('-c', '--collection', help='The collection code (e.g. VDB, BRIT)')
@click.option('-p', '--project', help='The project code (e.g. Crataegus, TX-digi)')
def main(directory=None, username=None, collection=None, project=None):
    # Gather session metadata in terminal prompts or command line switches
    # standalone_mode=False prevents click from exiting when all commands are complete
    # gather session information and start logging
    # Prompt user for parameters
    if not username:
        username = click.prompt('Please enter your first and last name')
        SESSION_LOGGER.info('username: ' + username)
        # session.username = session_username
    if not collection:
        collection = click.prompt('Please enter the collection code (e.g. VDB, BRIT)')
        SESSION_LOGGER.info('collection: ' + collection)
        # session.collection_code = session_collection
    if not project:
        project = click.prompt('Please enter the project code (use \'none\' if no project or unknown.)')
        SESSION_LOGGER.info('project: ' + project)
        # session.project = session_project
    if not directory:
        directory = click.prompt('Please enter the path of the session folder', type=click.Path(exists=True))
        SESSION_LOGGER.info('directory: ' + directory)
        # session.path = os.path.abspath(user_session_path)
    print('Monitoring session folder:', directory)
    print('Press Ctrl +  C to end session.')

    client = Client()
    client.session = Session(client_instance=client)
    client.session.path = os.path.abspath(directory)
    client.session.project_code = project
    client.session.collection_code = collection
    client.session.username = username

    # Set up session logging
    log_filename = str(client.session.uuid) + '.log'
    log_path = os.path.join(client.session.path, log_filename)
    SESSION_LOGGER.setLevel(logging.DEBUG)
    session_handler = logging.FileHandler(log_path)
    session_handler.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    session_handler.setFormatter(log_formatter)
    SESSION_LOGGER.addHandler(session_handler)
    SESSION_LOGGER.info('session.uuid: ' + client.session.uuid)
    SESSION_LOGGER.info('session.username: ' + client.session.username)
    SESSION_LOGGER.info('session.collection_code: ' + client.session.collection_code)
    SESSION_LOGGER.info('session.project_code: ' + client.session.project_code)
    SESSION_LOGGER.info('session.path: ' + client.session.path)
    # Set up cleanup actions
    # This may not be needed if Ctrl C works
    atexit.register(end_cli_session, session=client.session)

    # start watching session folder for file additions and changes
    event_handler = ImageHandler(session=client.session, patterns=IMAGE_PATTERNS)
    observer = Observer()
    observer.schedule(event_handler, client.session.path, recursive=True)
    observer.start()
    SESSION_LOGGER.info('Session monitor started.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Ending by KeyboardInterrupt')
        # For some reason, the atexit isn't always being triggered on Windows although the KeyboardInterrupt is registered
        # Manually calling end_cli_session
        # TODO need to test if session has been completed/terminated first, if not, call manually
        #end_cli_session(session=client.session)
    observer.join()

def end_cli_session(session=None):
    print('end_cli_session:', session.uuid)
    if session:
        print('Session monitoring ended')
        print('Session username: {}'.format(session.username))
        print('Session ID: {}'.format(session.uuid))
        print('Session path: {}'.format(session.path))
        print('Image event count:', len(session.image_events))

        for event in session.image_events:
            print(event.id, event.catalog_number)
            event.rename_files()
        #print('Completing final sync...STUB')
        # os.system("rsync -arz " + session['path'] + " /Users/jbest/Desktop/demo_shared")
        session = None

        SESSION_LOGGER.info('Session monitor terminated.')
    else:
        print('INFO - no session to end or session already ended.')
        SESSION_LOGGER.info('No session to end or session already ended.')
    quit()


if __name__ == '__main__':
    main()
