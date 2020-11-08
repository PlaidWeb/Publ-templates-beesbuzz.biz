""" unmangle the badly-mangled BBCode shit """

import sqlite3
import sys
import re
import html

db = sqlite3.connect(sys.argv[1])

for row in db.cursor().execute('select id,text from comments'):
    cid, text = row

    # unmangle doubly-nested a hrefs
    text = re.sub(r'&lt;a href=&quot;<a rel="nofollow" href="([^"]*)">[^<]*</a>&quot;&gt;(.*)&lt;/a&gt;',
                  r'<a href="\1">\2</a>', text)

    # unmangle other html
    text = re.sub(r'&quot;', r'"', text)
    text = re.sub(r'&lt;([^&]*)&gt;', r'<\1>', text)

    # unmangle bbcode
    text = re.sub(r'\[(/)?quote(:[a-z0-9]*)?([^\]]*)\]',
                  r'<\1blockquote>', text)
    text = re.sub(r'\[(/)?b(:[a-z0-9]*)?([^\]]*)\]', r'<\1strong>', text)
    text = re.sub(r'\[(/)?i(:[a-z0-9]*)?([^\]]*)\]', r'<\1em>', text)

    if text != row[1]:
        print(row, '\n ->\n', text, '\n\n')
        db.cursor().execute('update comments set text=? where id=?', (text, cid))

emap = {
    'wink': '😉',
    'shock': '😲',
    'twisted': '😈',
    'lol': '😂',
    'cry': '😢',
    'roll': '🙄',
    'oops': '😊'
}

emojis = set()
for row in db.cursor().execute('select id,text from comments where text like "%:%:%"'):
    cid, text = row
    for em in re.findall(r':([a-z]+):', text):
        emojis.add(em)
    for em, out in emap.items():
        text = text.replace(':' + em + ':', out)

    if text != row[1]:
        print(row, '\n ->\n', text, '\n\n')
        db.cursor().execute('update comments set text=? where id=?', (text, cid))

print(emojis)

db.commit()
