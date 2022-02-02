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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
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

        # create some test data in the database
        follow = Follows(user_following_id = 1, user_being_followed_id = 2)
        message = Message(text="Comment", user_id=1)
        db.session.add_all([follow, message])
        db.session.commit()

        # Does the repr method work as expected?
        self.assertEqual(f"<User #{u.id}: {u.username}, {u.email}>", u.__repr__())

        # Does is_following successfully detect when user1 is following user2?
        self.assertTrue(u.is_following(u2))

        # Does is_following successfully detect when user1 is not following user2?
        self.assertFalse(u2.is_following(u))

        # Does is_followed_by successfully detect when user1 is followed by user2?
        self.assertTrue(u2.is_followed_by(u))

        # Does is_followed_by successfully detect when user1 is not followed by user2?
        self.assertFalse(u.is_followed_by(u2))

        # Does User.create successfully create a new user given valid credentials?
        u3 = User.signup(username = 'username', email='test3@test.com', password='testpass', image_url = None)
        db.session.add(u3)
        db.session.commit()
        
        # test to see if correct information is saved
        self.assertEqual(u3.username, 'username')
        self.assertEqual(u3.email, 'test3@test.com')
        self.assertEqual(u3.image_url, '/static/images/default-pic.png')
        # Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?
        # self.assertRaises(TypeError, User.signup())
        with self.assertRaises(TypeError):
            User.signup()
        with self.assertRaises(IntegrityError):
            u4 = User.signup(username='username', email='test3@test.com', password='testpass', image_url=None)
            db.session.add(u4)
            db.session.commit()

        db.session.rollback()
        # Does User.authenticate successfully return a user when given a valid username and password?
        user = User.authenticate('username', 'testpass')
        self.assertEqual(user, u3)
        # Does User.authenticate fail to return a user when the username is invalid?
        self.assertFalse(User.authenticate('fake_user_name', 'testpass'))
        # Does User.authenticate fail to return a user when the password is invalid?
        self.assertFalse(User.authenticate('username', 'wrong_pass'))