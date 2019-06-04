"""Configure local and shared parameters for imaging client."""

import configparser
import os
import uuid

import click

config_local_path = 'config_local.ini'
config_path = 'config.ini'
config_local = configparser.ConfigParser(allow_no_value=True)
# TODO check if file exists

def main():
    if os.path.isfile(config_local_path):
        # config_local file exists
        print('The file ' + config_local_path + ' already exists.')
        print('Confirm the following parameters:')
        config_local.read(config_local_path)
        print(config_local)
    else:
        # Prompt for local config
        create_config_local()
        # print(station_uuid, station_id)


@click.command()
def create_config_local():
    click.echo('The config_local.ini file does not exist.')
    click.echo('Please provide the following information...')
    station_id = click.prompt('Enter a station identifier - this should be short and unique. (eg. \'S1\')')
    print('station_id:', station_id)
    print('Generating station UUID')
    station_uuid = str(uuid.uuid4())
    print('station_uuid:', station_uuid)
    write_config_local(station_uuid, station_id)


def write_config_local(station_uuid=None, station_id='UNSPECIFIED'):
    config_local['LOCAL'] = {}
    config_local.set('LOCAL', '# DO NOT SHARE config_local file between imaging stations.', None)
    config_local.set('LOCAL', '# The station_uuid must remain unique to each image station.', None)
    config_local['LOCAL']['station_uuid'] = station_uuid
    config_local['LOCAL']['station_id'] = station_id

    with open('config_local.ini', 'w') as config_local_file:
        config_local.write(config_local_file)

if __name__ == '__main__':
    main()
