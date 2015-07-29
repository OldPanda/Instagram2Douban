#!/bin/bash
# Backup every 1h at 1:15 2:15 ...
# 15 * * * * /bin/bash /home/wilbeibi/backups/mongo_backup.sh
MONGO_DATABASE="insdouban"
COLLECTION="users"


MONGO_HOST="127.0.0.1"
MONGO_PORT="27017"
TIMESTAMP=`date +%F-%H-%M`
MONGOEXPORT_PATH="/usr/bin/mongoexport"
BACKUPS_DIR="/home/wilbeibi/backups/"
BACKUP_NAME="$BACKUPS_DIR$TIMESTAMP.json"

# mongo admin --eval "printjson(db.fsyncLock())"
# $MONGODUMP_PATH -h $MONGO_HOST:$MONGO_PORT -d $MONGO_DATABASE
$MONGOEXPORT_PATH --db $MONGO_DATABASE --collection $COLLECTION --out $BACKUP_NAME
# mongo admin --eval "printjson(db.fsyncUnlock())"  
