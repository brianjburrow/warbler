"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

            # GET request to new messages
            resp = c.get('/messages/new')
            html = resp.get_data(as_text=True)
            
            self.assertIn('<div class="navbar-header">', html)
            self.assertIn('text', html)
        
    def test_view_message(self):
        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            msg = Message.query.one()

            resp = c.get(f"/messages/{msg.id}")

            html = resp.get_data(as_text=True)
            
            # test that 'base.html' is imported, thus bringing in navbar
            self.assertIn('class="navbar navbar-expand"', html)
            
            # test that delete is shown for the correct user
            self.assertIn(f'/messages/{msg.id}/delete"', html)

            # test that unfollow is not displayed
            self.assertNotIn('Unfollow', html)

            # test that Follow is not displayed (cannot follow yourself)
            self.assertNotIn('Follow', html)
            
    def test_delete_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id 

            # make a new message
            resp = c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.one()

            resp = c.post(f"messages/{msg.id}/delete")

            self.assertEqual(resp.status_code, 302)

    def test_new_message_unauthorized(self):
        with self.client as c:
            resp = c.post('/messages/new', data={"text": "Hello"})
            
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/messages/new', data={"text":"Hello"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)

            self.assertIn("Access unauthorized.",html)
    
    def test_delete_message_unauthorized(self):
        with self.client as c:
            resp = c.post('/messages/1/delete')
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/messages/1/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized", html)

    








    


