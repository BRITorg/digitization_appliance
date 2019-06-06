"""Configure local and shared parameters for imaging client."""

import configparser
import os
import uuid

import click

config_local_path = 'config_local.ini'
config_path = 'config.ini'
config_local = configparser.ConfigParser(allow_no_value=True)


def main():
    """Create config_local file or, if it exists, display the settings."""
    if os.path.isfile(config_local_path):
        # config_local file exists
        print('The file ' + config_local_path + ' already exists.')
        print('Confirm the following parameters:')
        config_local.read(config_local_path)
        for section in config_local.sections():
            print(section)
            for key, value in config_local.items(section):
                print(key, value)
    else:
        # Prompt for local_config settings.
        create_config_local()


@click.command()
def create_config_local():
    """
    Create a new config_local file.

    This function prompts the user to enter a station_id
    and automatically generates a UUID used for the station_uuid.
    This file contains settings that should be unique to each image station
    and the file should not be shared or copied between stations.
    """
    click.echo('The config_local.ini file does not exist.')
    click.echo('Please provide the following information...')
    station_id = click.prompt('Enter a station identifier - this should be short and unique. (eg. \'S1\')')
    print('station_id:', station_id)
    print('Generating station UUID')
    station_uuid = str(uuid.uuid4())
    print('station_uuid:', station_uuid)
    write_config_local(station_uuid, station_id)


def write_config_local(station_uuid=None, station_id='UNSPECIFIED'):
    """Write the config_local file."""
    config_local['LOCAL'] = {}
    config_local.set('LOCAL', '# DO NOT SHARE config_local file between imaging stations.', None)
    config_local.set('LOCAL', '# The station_uuid must remain unique to each image station.', None)
    config_local['LOCAL']['station_uuid'] = station_uuid
    config_local['LOCAL']['station_id'] = station_id

    with open('config_local.ini', 'w') as config_local_file:
        config_local.write(config_local_file)

    print('Configuration file created:', config_local_path)

if __name__ == '__main__':
    main()
