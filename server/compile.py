import argparse
import glob
import json
import os
import sqlite3 as lite

# set up argument parser
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--source", required=True, \
                help="Path to the directory that contains the images to be analyzed.")

"""
ap.add_argument("-o", "--output", required=False, \
    help="Path to the directory where log file is written.")
"""
args = vars(ap.parse_args())

# set up database
conn = lite.connect('session_images.db')
cur = conn.cursor()
try:
    cur.execute('''CREATE TABLE images (id INTEGER PRIMARY KEY, \
        session_uuid text, \
        session_path text, \
        creator text, \
        collection_code text, \
        project_code text, \
        session_notes text, \
        session_taxa text, \
        station_code text, \
        uuid text, \
        status text, \
        original_raw_image text, \
        new_raw_image text, \
        raw_image_creation_date text, \
        raw_image_md5hash text, \
        original_derived_image text, \
        new_derived_image text, \
        original_filename text, \
        catalog_number text, \
        sequence text)''')
except lite.Error as e:
    print(e)
"""
# set up database
conn = lite.connect('workflow.db')
cur = conn.cursor()
try:
    cur.execute('''CREATE TABLE images (id INTEGER PRIMARY KEY, \
        batch_id text, batch_path text, batch_flags text, project_id text, \
        image_event_id text, datetime_analyzed text, \
        barcodes text, image_classifications text, closest_model text, \
        image_path text, basename text, file_name text, file_extension text, \
        file_creation_time text, file_hash text, file_uuid text, derived_from_file text)''')
except lite.Error as e:
    print(e)
"""

directory_path = os.path.realpath(args["source"])
print('Scanning directory:', directory_path)
for file_path in sorted(glob.glob(os.path.join(directory_path, '*.JSON')), key=os.path.getmtime): #this file search seems to be case sensitive
    print(file_path)
    with open(file_path) as f:
        d = json.load(f)
        print(d['session_uuid'])
        # insert into database
        cur.execute(\
        "INSERT INTO images ( \
            session_uuid, \
            session_path, \
            creator, \
            collection_code, \
            project_code, \
            session_notes, \
            session_taxa, \
            station_code, \
            uuid, \
            status, \
            original_raw_image, \
            new_raw_image, \
            raw_image_creation_date, \
            raw_image_md5hash, \
            original_derived_image, \
            new_derived_image, \
            original_filename, \
            catalog_number, \
            sequence \
        )\
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,?, ?, ?, ?, ? ,?)", \
        ( \
            d['session_uuid'], \
            d['session_path'], \
            d['creator'], \
            d['collection_code'], \
            d['project_code'], \
            d['session_notes'], \
            d['session_taxa'], \
            d['station_code'], \
            d['id'], \
            d['status'], \
            d['original_raw_image'], \
            d['new_raw_image'], \
            d['raw_image_creation_date'], \
            d['raw_image_md5hash'], \
            d['original_derived_image'], \
            d['new_derived_image'], \
            d['original_filename'], \
            d['catalog_number'], \
            d['sequence'] \
        ))
    conn.commit()
"""
'session_uuid'
'session_path'
'creator'
'collection_code'
'project_code'
'session_notes'
'session_taxa'
'station_code'
'id'
'status'
'original_raw_image'
'new_raw_image'
'raw_image_creation_date'
'raw_image_md5hash'
'original_derived_image'
'new_derived_image'
'original_filename'
'catalog_number'
'sequence'
"""
