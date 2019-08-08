""" reimport comments that import-mt.py missed


pipenv run python3 -m migrations.import-mt-specific ~/Desktop/beesbuzz_mt.db beesbuzz.biz.db

"""

import sqlite3
import app
import sys
from publ import model, entry
from pony import orm
import arrow

mt = sqlite3.connect(sys.argv[1])
isso = sqlite3.connect(sys.argv[2])

@orm.db_session()
def do_one(entry_id, mt_id):
    with app.app.test_request_context():
        record = model.Entry.get(id=entry_id)
        e = entry.Entry(record)
        migrate(e, mt_id)

def get_thread(entry, old_id):
    uri = app.thread_id(entry)
    thread = isso.cursor().execute(
        "SELECT id FROM threads WHERE uri=?",
        (uri, )).fetchone()

    if not thread:
        print(f"Thread {old_id} not found; creating")
        isso.cursor().execute("""
            INSERT INTO threads (uri, title) VALUES (?, ?)
            """, (uri, entry._record.title))
        thread = isso.cursor().execute(
            "SELECT id FROM threads WHERE uri=?",
            (uri, )).fetchone()

    thread, = thread
    return thread

def migrate(entry, mt_id):
    print(entry.id, entry.title)

    comments = mt.cursor().execute("""
        SELECT
            comment_author,
            comment_email,
            comment_text,
            comment_url,
            comment_created_on,
            comment_ip
        FROM mt_comment as c
        LEFT JOIN mt_entry as e ON c.comment_entry_id = e.entry_id
        WHERE comment_entry_id = ?
        """, (mt_id,))

    for row in comments:
        thread = get_thread(entry, mt_id)
        author, email, text, url, date, remote_addr = row

        if not author:
            author = 'Anonymous'

        date = int(arrow.get(date, tz='US/Mountain').format('X'))

        print(f'{author} ({email}, {url}), {remote_addr} @ {date}:\n{text}')
        isso.cursor().execute("""
            INSERT INTO comments (tid, author, email, website, created, remote_addr, text, voters, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, '', 1)
            """, (thread, author, email, url, date, remote_addr, text))


# do_one(188, 353)  # growth spurt[s]
# do_one(312, 357) # west nile -> itch
# do_one(147, 369) # aquatic automobile [door prize]
# do_one(321, 407) # children should only be allowed on [air]planes as cargo
isso.commit()
