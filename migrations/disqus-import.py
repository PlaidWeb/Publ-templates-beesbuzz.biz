""" attempt to migrate mt_foo threads to new-Publ threads """

import app
import sys
from xml.etree import ElementTree
from publ import model, entry
from pony import orm
import logging
import sqlite3
from time import mktime, strptime

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


@orm.db_session
def build_uri_map():
    """ Map Disqus thread-ids to tuple of (isso_uri, title) """
    with app.app.test_request_context():
        uri_map = {}
        for record in model.Entry.select():
            e = entry.Entry(record)
            thread_id = e.get('thread-id', 'publ_{}'.format(record.id))
            uri_map[thread_id] = (app.thread_id(e), record.title)
        return uri_map


def parse_disqus(xmlfile, isso_db):
    ns = '{http://disqus.com}'
    internals = '{http://disqus.com/disqus-internals}'

    tree = ElementTree.parse(xmlfile)

    # map disqus id -> isso URI
    uri_map = build_uri_map()

    # map disqus dsq:id -> isso tid
    thread_map = {}

    for thread in tree.findall(ns + 'thread'):
        dsq_id = thread.attrib.get(internals + 'id')
        thread_id = thread.find(ns + 'id')
        if thread_id is None or not thread_id.text:
            continue

        LOGGER.info("mapping thread %s", thread_id.text)
        if thread_id.text not in uri_map:
            LOGGER.info("  entry not found")
            continue

        cursor = isso_db.cursor()

        isso_uri, title = uri_map[thread_id.text]
        if cursor.execute('SELECT * from threads WHERE uri=?', (isso_uri,)).fetchone():
            LOGGER.info("  Already have a thread for %s", thread_id)
            continue

        cursor.execute(
            'INSERT INTO threads (uri,title) VALUES (?,?)', (isso_uri, title))
        thread_map[dsq_id] = cursor.lastrowid

    # map disqus post id to isso id
    post_map = {}

    for post in tree.findall(ns + 'post'):
        thread_id = post.find(ns + 'thread').attrib.get(internals + 'id')
        if thread_id not in thread_map:
            continue

        parent_post = post.find(ns + 'parent')
        if parent_post is not None:
            parent_cid = post_map.get(parent_post.attrib.get(internals + 'id'))
        else:
            parent_cid = None

        cursor = isso_db.cursor()

        values = (
            thread_map[thread_id],
            parent_cid,
            post.find(ns+'author').find(ns+'name').text,
            mktime(strptime(post.find(ns+'createdAt').text, '%Y-%m-%dT%H:%M:%SZ')),
            post.find(ns + 'message').text,
            1 if post.find(ns + 'isDeleted').text == "false" else 4
        )
        cursor.execute(
            "INSERT INTO comments (tid, parent, author, created, remote_addr, text, voters, mode) VALUES (?,?,?,?,'0.0.0.0',?,'',?)", values)
        post_map[post.attrib.get(internals + 'id')] = cursor.lastrowid
        LOGGER.info("%s -> %s", cursor.lastrowid, values)

    LOGGER.info("Inserted %d posts", len(post_map))


isso_db = sqlite3.connect(sys.argv[2])
parse_disqus(sys.argv[1], isso_db)
isso_db.commit()
