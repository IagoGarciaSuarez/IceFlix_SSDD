import sqlite3
from os import listdir, remove
from os.path import isfile, join
import hashlib
import json
import itertools

SERVER_MEDIA_DIR = 'resources/'
CLIENT_MEDIA_DIR = 'client_media/'
CHUNK_SIZE = 4094
SPINNER = itertools.cycle(['|', '/', '-', '\\'])
CRED_DATABASE_PATH = 'persistence/credentialsDB/'
CATALOG_DATABASE_PATH = 'persistence/catalogDB/'
TAGS_DB = CATALOG_DATABASE_PATH + 'tagsDB.json'
CATALOG_DB = 'catalog.db'
ICEFLIX_BANNER = """
  ___         _____ _ _      
 |_ _|___ ___|  ___| (_)_  __
  | |/ __/ _ \ |_  | | \ \/ /
  | | (_|  __/  _| | | |>  < 
 |___\___\___|_|   |_|_/_/\_\
                             
"""

class CatalogDB():
    def __init__(self, database):
        self.database = CATALOG_DATABASE_PATH + database

    def _create_connection(self, database_file):
        conn = None
        try:
            conn = sqlite3.connect(database_file)
            conn.row_factory = lambda cursor, row: row[0]
            return conn

        except Exception as e:
            print(e)

        return conn
        
    def drop_table(self):
        drop_table_sql = 'DROP TABLE IF EXISTS catalog'
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(drop_table_sql)
        conn.close()

    def create_table(self):
        create_table_sql = 'CREATE TABLE IF NOT EXISTS catalog (id text PRIMARY KEY,initialName text NOT NULL);'
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
        conn.close()

    def get_all(self):
        get_all_sql = 'SELECT * FROM catalog'
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(get_all_sql)
            result = cursor.fetchall()
        conn.close()
        return result

    def is_in_catalog(self, media_id):
        exist_sql = f"SELECT * FROM catalog WHERE EXISTS(SELECT 1 FROM catalog WHERE id='{media_id}');"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(exist_sql)
            result = False
            if cursor.fetchone():
                result = True
        conn.close()
        return result

    def add_media(self, media_id, initial_name):
        add_sql = f"INSERT INTO catalog VALUES('{media_id}','{initial_name}')"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(add_sql)
            conn.commit()
        conn.close()

    def get_id_by_name(self, name, exact):
        if exact:
            get_id_by_name_sql = f"SELECT id FROM catalog WHERE initialName='{name}' COLLATE NOCASE"

        else:
            get_id_by_name_sql = f"SELECT id FROM catalog WHERE initialName LIKE '%{name}%' COLLATE NOCASE"

        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(get_id_by_name_sql)
            result = cursor.fetchall()
        return result
    
    def get_name_by_id(self, media_id):
        get_by_name_sql = f"SELECT initialName FROM catalog WHERE id='{media_id}'"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(get_by_name_sql)
            result = cursor.fetchone()
        return result

    def rename_media(self, media_id, name):
        rename_media_sql = f"UPDATE catalog SET initialName='{name}' WHERE id='{media_id}'"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(rename_media_sql)
            conn.commit()
        conn.close()

#=================== GENERAL FUNCTIONS ===================

def get_sha256(filename):
    sha256_hash = hashlib.sha256()
    with open(filename,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
    f.close()
    return sha256_hash.hexdigest()

def list_files(path):
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    return onlyfiles

def remove_file(id):
    for media in list_files(SERVER_MEDIA_DIR):
        if get_sha256(SERVER_MEDIA_DIR + media) == id:
            remove(SERVER_MEDIA_DIR + media)
            return True
    return False
    
def read_tags_db(tags_db):
    tags_db = CATALOG_DATABASE_PATH + tags_db
    with open(tags_db, 'r') as f:
            tags = json.load(f)
            f.close()
    return tags

def write_tags_db(tags, tags_db):
    tags_db = CATALOG_DATABASE_PATH + tags_db
    with open(tags_db, 'w') as f:
        json.dump(tags, f)
        f.close()

def read_cred_db(credentials_db):
    credentials_db = CRED_DATABASE_PATH + credentials_db
    with open(credentials_db, 'r') as f:
        cred_db = json.load(f)
        f.close()
    return cred_db

def write_cred_db(credentials, credentials_db):
    credentials_db = CRED_DATABASE_PATH + credentials_db
    with open(credentials_db, 'w') as f:
        json.dump(credentials, f)
        f.close()

def getPasswordSHA256(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()