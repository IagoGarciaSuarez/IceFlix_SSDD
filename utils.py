'''Clase con funciones varias y la implemenación del objeto CatalogDB para accesos al catálogo.'''
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
  | |/ __/ _ \\ |_  | | \\ \\/ /
  | | (_|  __/  _| | | |>  < 
 |___\\___\\___|_|   |_|_/_/\\_\\
                             
"""


class CatalogDB():
    '''Objeto para acceso a la db del catálogo'''
    def __init__(self, database):
        '''Selección de la base de datos.'''
        self.database = CATALOG_DATABASE_PATH + database

    def _create_connection(self, database_file): # pylint: disable=no-self-use
        '''Crea la conexión.'''
        conn = sqlite3.connect(database_file)
        conn.row_factory = lambda cursor, row: row[0]
        return conn

    def drop_table(self):
        '''Vacía la base de datos.'''
        drop_table_sql = 'DROP TABLE IF EXISTS catalog'
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(drop_table_sql)
        conn.close()

    def create_table(self):
        '''Crea una tabla si no existe.'''
        create_table_sql = 'CREATE TABLE IF NOT EXISTS catalog ' + \
            '(id text PRIMARY KEY,initialName text NOT NULL);'
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
        conn.close()

    def get_all(self):
        '''Devuelve todos los registros.'''
        get_all_sql = 'SELECT * FROM catalog'
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(get_all_sql)
            result = cursor.fetchall()
        conn.close()
        return result

    def is_in_catalog(self, media_id):
        '''Comprueba si está en la bbdd.'''
        exist_sql = "SELECT * FROM catalog WHERE EXISTS(SELECT 1 " + \
            f"FROM catalog WHERE id='{media_id}');"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(exist_sql)
            result = False
            if cursor.fetchone():
                result = True
        conn.close()
        return result

    def add_media(self, media_id, initial_name):
        '''Añade un nuevo medio al catálogo.'''
        add_sql = f"INSERT INTO catalog VALUES('{media_id}','{initial_name}')"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(add_sql)
            conn.commit()
        conn.close()

    def get_id_by_name(self, name, exact):
        '''Obtiene el id según el nombre.'''
        if exact:
            get_id_by_name_sql = f"SELECT id FROM catalog WHERE initialName='{name}' " + \
                "COLLATE NOCASE"

        else:
            get_id_by_name_sql = f"SELECT id FROM catalog WHERE initialName LIKE '%{name}%' " + \
                "COLLATE NOCASE"

        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(get_id_by_name_sql)
            result = cursor.fetchall()
        return result

    def get_name_by_id(self, media_id):
        '''Obtiene el nombre según el id.'''
        get_by_name_sql = f"SELECT initialName FROM catalog WHERE id='{media_id}'"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(get_by_name_sql)
            result = cursor.fetchone()
        return result

    def rename_media(self, media_id, name):
        '''Renombra un registro.'''
        rename_media_sql = f"UPDATE catalog SET initialName='{name}' WHERE id='{media_id}'"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(rename_media_sql)
            conn.commit()
        conn.close()

    def remove_media(self, media_id):
        '''Elimina un registro.'''
        remove_media_sql = f"DELETE FROM catalog WHERE id='{media_id}'"
        with self._create_connection(self.database) as conn:
            cursor = conn.cursor()
            cursor.execute(remove_media_sql)
            conn.commit()
        conn.close()

# =================== GENERAL FUNCTIONS ===================

def get_sha256(filename):
    '''Genera el sha256 de un archivo.'''
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)
    file.close()
    return sha256_hash.hexdigest()

def list_files(path):
    '''Lista todos los archivos de un directorio.'''
    onlyfiles = [file for file in listdir(path) if isfile(join(path, file))]
    return onlyfiles

def remove_file(media_id):
    '''Elimina un archivo.'''
    for media in list_files(SERVER_MEDIA_DIR):
        if get_sha256(SERVER_MEDIA_DIR + media) == media_id:
            remove(SERVER_MEDIA_DIR + media)
            return True
    return False

def read_tags_db(tags_db):
    '''Lee la base de datos de tags.'''
    tags_db = CATALOG_DATABASE_PATH + tags_db
    with open(tags_db, 'r') as file:
        tags = json.load(file)
        file.close()
    return tags

def write_tags_db(tags, tags_db):
    '''Sobreescribe en la base de datos de tags.'''
    tags_db = CATALOG_DATABASE_PATH + tags_db
    with open(tags_db, 'w') as file:
        json.dump(tags, file)
        file.close()

def read_cred_db(credentials_db):
    '''Lee la base de datos de las credenciales.'''
    credentials_db = CRED_DATABASE_PATH + credentials_db
    with open(credentials_db, 'r') as file:
        cred_db = json.load(file)
        file.close()
    return cred_db

def write_cred_db(credentials, credentials_db):
    '''Sobreescribe en la base de datos de las credenciales.'''
    credentials_db = CRED_DATABASE_PATH + credentials_db
    with open(credentials_db, 'w') as file:
        json.dump(credentials, file)
        file.close()

def get_password_sha256(password):
    '''Genera el sha256 de una password.'''
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
