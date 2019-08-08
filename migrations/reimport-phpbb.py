""" reimport the old comments from the phpbb_integrate database """

import sqlite3
import app
import sys
from publ import model, entry
from pony import orm
import bbcode
import socket
import struct

phpbb = sqlite3.connect(sys.argv[1])
isso = sqlite3.connect(sys.argv[2])

@orm.db_session()
def do_all():
    with app.app.test_request_context():
        for record in model.Entry.select():
            e = entry.Entry(record)
            migrate(e)

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

def migrate(entry):
    old_id = entry.get('thread-id')
    if not old_id or not old_id.startswith('mt_'):
        return

    print(entry.id, entry.title)

    comments = phpbb.cursor().execute("""
        SELECT
            CASE p.poster_id
                WHEN -1 THEN p.post_username
                ELSE u.username
            END,
            u.user_email,
            pt.post_text,
            p.post_time,
            u.user_website,
            p.poster_ip
        FROM phpbb_integrate AS i
        LEFT JOIN phpbb_topics AS t ON i.topic = t.topic_id
        LEFT JOIN phpbb_posts AS p on p.topic_id = t.topic_id
        LEFT JOIN phpbb_posts_text AS pt ON pt.post_id = p.post_id
        LEFT JOIN phpbb_users AS u ON p.poster_id = u.user_id
        WHERE i.source = ? AND p.poster_id != 13
        """, (old_id,))

    for row in comments:
        thread = get_thread(entry, old_id)
        username, email, post_text, date, website, remote_addr = row

        if not username:
            username = 'Anonymous'

        post_text = ('<p>' + bbcode.render_html(post_text) + '</p>').replace('<br /><br />', '</p><p>')

        remote_addr = socket.inet_ntoa(struct.pack("!I", int(remote_addr,16)))

        print(f'{username} ({email}, {website}), {remote_addr} @ {date}:\n{post_text}')
        isso.cursor().execute("""
            INSERT INTO comments (tid, author, email, website, created, remote_addr, text, voters, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, '', 1)
            """, (thread, username, email, website, date, remote_addr, post_text))


do_all()
isso.commit()
