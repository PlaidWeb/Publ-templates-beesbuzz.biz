""" Script to refresh comment thread IDs after updating the security token

usage:

    pipenv run python3 update-thread-ids.py /path/to/comments.db

"""

import sys
import app
import sqlite3
import re
from publ import model, entry
from pony import orm

db = sqlite3.connect(sys.argv[1])

@orm.db_session()
def update_thread(tid, uri):
    match = re.match(r'/[a-f0-9]{16}/([0-9]*)$', uri)
    if not match:
        return

    entry_id = int(match.group(1))
    record = model.Entry.get(id=entry_id)
    if not record:
        print("Couldn't find entry", entry_id)
        return

    with app.app.test_request_context():
        e = entry.Entry(record)
        new_uri = app.thread_id(e)
        if new_uri != uri:
            print(uri, '\t->', new_uri)
            db.cursor().execute('UPDATE threads SET uri=?, title=? where id=?', (app.thread_id(e), record.title, tid))

for row in db.cursor().execute('SELECT id,uri FROM threads'):
    tid, uri = row
    update_thread(tid, uri)

db.commit()