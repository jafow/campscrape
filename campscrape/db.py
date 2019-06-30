""" db """
from datetime import datetime
from hashlib import md5
import logging
import sqlite3

logger = logging.getLogger(__name__)

class ContentDb():
    def __init__(self, db):
        self.db = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)
        self.db.row_factory = sqlite3.Row
        self.run_setup()

    def close(self):
        """ close the db connection """
        self.db.close()

    def run_setup(self):
        """ setup the schema """
        with open('campscrape/schema.sql', 'rb') as f:
            self.db.executescript(f.read().decode('utf8'))
        self.db.create_function("hasher", 1, self._digest)
        self.db.commit()

    def _digest(self, b):
        return md5(b).digest()

    def lookup_contenthash(self):
        """ lookup content """
        logger.info("Looking up content for msg")
        sql = "select id from messages where content=(?)"
        return sql

    def write_contenthash(self):
        """ insert content """
        logger.info("Inserting content for msg")
        sql = """ insert into messages(content, created_at)
        values (?, ?)"""
        return sql

    def get_set(self, contentbytes):
        """ do a lookup for contenthash and set if not exists """
        res = None
        cur = self.db.cursor()
        cur.execute(self.lookup_contenthash(), (self._digest(contentbytes),))

        if cur.fetchone() is None:
            # new msg, write it
            logger.info("New message writing to db")
            now = datetime.utcnow()
            cur.execute(self.write_contenthash(), (self._digest(contentbytes), now,))
            self.db.commit()
            res = 0
        else:
            # we've seen this content before dont write
            logger.info("skipping write on message seen previously")
            res = 1
        cur.close()
        return res


# db instance
db = ContentDb('campscrape.db')
