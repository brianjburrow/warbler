"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy.exc import IntegrityError
# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app
app.config['TESTING'] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_message_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email='test2@test.com',
            username='testuser2',
            password='HASHED_PASSWORD_2'
        )

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


        follow = Follows(user_following_id = 1, user_being_followed_id = 2)
        message = Message(text="Comment", user_id=1)
        db.session.add_all([follow, message])
        db.session.commit()

        # Does the repr method work as expected?
        self.assertEqual(message.__repr__(), f"<Message #{message.id} created at {message.timestamp} by User #{message.user_id} with message: {message.text}")
        
        # Does the user relationship work as expected?
        self.assertEqual(u, message.user)
        self.assertEqual(u.id, message.user_id)

