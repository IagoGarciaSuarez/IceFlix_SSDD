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
DATABASE_PATH = 'persistence/'
TAGS_DB = DATABASE_PATH + 'tagsDB.json'
CREDENTIALS_DB = DATABASE_PATH + 'credentials.json'
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
        self.database = DATABASE_PATH + database

    def _create_connection(self, database_file):
        conn = None
        try:
            conn = sqlite3.connect(database_file)
            conn.row_factory = lambda cursor, row: row[0]
            return conn

        except Exception as e:
            print(e)

        return conn
        
    def _drop_table(self):
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

    def getAll(self):
        getAll_sql = 'SELECT * FROM catalog'
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(getAll_sql)
            result = cursor.fetchall()
        conn.close()
        return result

    def isInCatalog(self, id):
        exist_sql = f"SELECT * FROM catalog WHERE EXISTS(SELECT 1 FROM catalog WHERE id='{id}');"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(exist_sql)
            result = False
            if cursor.fetchone():
                result = True
        conn.close()
        return result

    def addMedia(self, id, initialName):
        add_sql = f"INSERT INTO catalog VALUES('{id}','{initialName}')"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(add_sql)
            conn.commit()
        conn.close()

    def getIdByName(self, name, exact):
        if exact:
            getIdByName_sql = f"SELECT id FROM catalog WHERE initialName='{name}' COLLATE NOCASE"

        else:
            getIdByName_sql = f"SELECT id FROM catalog WHERE initialName LIKE '%{name}%' COLLATE NOCASE"

        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(getIdByName_sql)
            result = cursor.fetchall()
        return result
    
    def getNameById(self, id):
        getByName_sql = f"SELECT initialName FROM catalog WHERE id='{id}'"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(getByName_sql)
            result = cursor.fetchone()
        return result

    def renameMedia(self, id, name):
        renameMedia_sql = f"UPDATE catalog SET initialName='{name}' WHERE id='{id}'"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(renameMedia_sql)
            conn.commit()
        conn.close()

#=================== GENERAL FUNCTIONS ===================

def getSHA256(filename):
    sha256_hash = hashlib.sha256()
    with open(filename,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)
    f.close()
    return sha256_hash.hexdigest()

def listFiles(path):
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    return onlyfiles

def removeFile(id):
    for media in listFiles(SERVER_MEDIA_DIR):
        if getSHA256(SERVER_MEDIA_DIR + media) == id:
            remove(SERVER_MEDIA_DIR + media)
            return True
    return False
    
def readTagsDB():
    with open(TAGS_DB, 'r') as f:
            tagsDB = json.load(f)
            f.close()
    return tagsDB

def writeTagsDB(tagsDB):
    with open(TAGS_DB, 'w') as f:
        json.dump(tagsDB, f)
        f.close()

def readCredDB():
    with open(CREDENTIALS_DB, 'r') as f:
        credDB = json.load(f)
        f.close()
    return credDB

def writeCredDB(credDB):
    with open(CREDENTIALS_DB, 'w') as f:
        json.dump(credDB, f)
        f.close()

def getPasswordSHA256(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()