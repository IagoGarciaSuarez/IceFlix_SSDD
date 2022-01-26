shopt -s extglob
rm -- persistence/catalogDB/!(catalog.db|tagsDB.json)
rm -- persistence/credentialsDB/!(credentials.json)