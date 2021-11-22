import sqlite3

class CatalogDB():
    def __init__(self, database):
        self._connection = self._create_connection(database)
        self._cursor = self._connection.cursor()
        if self._connection is not None:
            self._create_table()

    def _create_connection(self, database_file):
        conn = None
        try:
            conn = sqlite3.connect(database_file)
            return conn

        except Exception as e:
            print(e)

        return conn

    def _create_table(self):
        create_table_sql = 'CREATE TABLE IF NOT EXISTS catalog (id text PRIMARY KEY,initialName text NOT NULL);'
        try:
            c = self._connection.cursor()
            c.execute(create_table_sql)
        except Exception as e:
            print(e)

    def getAll(self):
        getAll_sql = 'SELECT * FROM catalog'

        self._cursor.execute(getAll_sql)
        
        return self._cursor.fetchall()

    def isInCatalog(self, id):
        exist_sql = f"SELECT * FROM catalog WHERE EXISTS(SELECT 1 FROM catalog WHERE id='{id}');"
        self._cursor.execute(exist_sql)
        if self._cursor.fetchone():
            return True
        return False

    def addMedia(self, id, initialName):
        add_sql = f"INSERT INTO catalog VALUES('{id}','{initialName}')"

        self._cursor.execute(add_sql)
        self._connection.commit()

    def getByName(self, name):
        getByName_sql = f"SELECT * FROM catalog WHERE initialName='{name}'"

        self._cursor.execute(getByName_sql)
        
        return self._cursor.fetchall()

    def getWithName(self, name):
        getByName_sql = f"SELECT * FROM catalog WHERE initialName LIKE '%{name}%'"

        self._cursor.execute(getByName_sql)
        
        return self._cursor.fetchall()


    def closeConnection(self):
        self._connection.close()