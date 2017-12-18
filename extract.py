import re
import requests
import sqlite3
import html

from enum import Enum
from functools import reduce
import sys
import math
import datetime, time

class TicketState(Enum):
    UNREAD = "unread"
    OPENED = "opened"
    PENDING = "pending"
    CLOSED = "closed"
    SPAM = "spam"

class GrooveClient(object):

    def __init__(self, token):
        self._token = token
        self._session = requests.Session()
        self._session.headers = self._headers()

    def _headers(self):
        return {'Authorization': 'Bearer {}'.format(self._token)}

    def get(self, path, **kwargs):
        params = { k:v for k, v in kwargs.items() }
        resp = self._session.get('https://api.groovehq.com/v1/%s' % path,
                                 params=params)
        return resp.json()

    def get_tickets(self, **kwargs):
        return self.get('tickets', **kwargs)['tickets']

    def get_customers(self, **kwargs):
        return self.get('customers', **kwargs)['customers']

    def get_ticket_state(self, ticket_id, **kwargs):
        return self.get('tickets/%s/state' % ticket_id, **kwargs)['state']

    def get_mailboxes(self):
        return self.get('mailboxes')["mailboxes"]

    def get_folders(self):
        return self.get('folders')["folders"]

    def get_ticket_counts(self, **kwargs):
        return self.get('tickets/count', **kwargs)

    def get_messages(self, ticket_id, **kwargs):
        return self.get('tickets/%s/messages' % ticket_id, **kwargs)['messages']

conn = sqlite3.connect('groove.sqlite')
c = conn.cursor()
c.execute('''CREATE TABLE tickets
             (ticket_id integer, created_at text, title text, state integer)''')

c.execute('''CREATE TABLE messages
             (ticket_id integer, message_id integer, created_at text, author text, body text)''')

c.execute('''CREATE INDEX idx_tickets_id  ON tickets (ticket_id);''')
c.execute('''CREATE INDEX idx_tickets_created_at  ON tickets (created_at);''')
c.execute('''CREATE INDEX idx_tickets_state  ON tickets (state);''')

c.execute('''CREATE INDEX idx_messages_ticket_id  ON messages (ticket_id);''')
c.execute('''CREATE INDEX idx_messages_message_id  ON messages (message_id);''')
c.execute('''CREATE INDEX idx_messages_created_at  ON messages (created_at);''')
c.execute('''CREATE INDEX idx_messages_author  ON messages (author);''')

client = GrooveClient(sys.argv[1])
ticket_counts = client.get_ticket_counts()
total_tickets = reduce(lambda x, y: x + y, ticket_counts.values())
ticket_pages = math.ceil(total_tickets / 50)

ticket_ids = []

for i in range(1, ticket_pages + 1):
    percent = math.ceil((i / ticket_pages) * 100)
    sys.stdout.write("\rFetching tickets %d%%" % percent)
    sys.stdout.flush()
    tickets = client.get_tickets(page=i, per_page=50)
    for ticket in tickets:
        ticket_id = ticket["number"]
        ticket_ids.append(ticket_id)
        title = ticket["title"]
        created_at = ticket["created_at"]
        c.execute("INSERT INTO tickets (ticket_id, created_at, title, state) VALUES (?,?,?,?)", (ticket_id, created_at, title, ""))

total = 0
sys.stdout.write("\n")
for ticket_id in ticket_ids:
    total += 1
    percent = math.ceil(total / len(ticket_ids) * 100)
    sys.stdout.write("\rMessages %d%%" % percent)
    sys.stdout.flush()
    messages = client.get_messages(ticket_id)
    for message in messages:
        message_id = message["id"]
        author_link = message["links"]["author"]["href"]
        author = re.search(r".*/([^/]+)$", author_link).group(1)
        created_at = message["created_at"]
        body = html.unescape(message["plain_text_body"])
        c.execute("""INSERT INTO messages
            (ticket_id, message_id, created_at, author, body)
            VALUES (?,?,?,?,?)""",
            (ticket_id, message_id, created_at, author, body))
    state = TicketState(client.get_ticket_state(i))
    state_id = list(TicketState).index(state)
    c.execute('''UPDATE tickets SET state = ? WHERE ticket_id = ?''', (state_id, ticket_id))

conn.commit()
conn.close()
sys.stdout.write("\n")