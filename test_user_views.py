"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows

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

        user2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        user3 = User.signup(username="testuser3",
                                    email="test3@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
        follow_list = [Follows(user_being_followed_id = user2.id, user_following_id=self.testuser.id),
        Follows(user_being_followed_id = self.testuser.id, user_following_id=user2.id)]
        db.session.add_all(follow_list)
        db.session.commit()

        self.user2_id = user2.id 
        self.user3_id = user3.id
        pass

    def test_login(self):
        '''Can we login'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # test GET response
            resp = c.get('/login')
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)

            self.assertIn("Welcome back.", html)
            self.assertIn('form method="POST" id="user_form"', html)

            # test POST response, valid credentials
            resp = c.post('/login', data = {'username':'testuser', 'password':"testuser"})
            self.assertEqual(resp.status_code, 302)

            resp = c.post('/login', data = {'username':'testuser', 'password':"testuser"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn(f"Hello, {self.testuser.username}",html)


    def test_login_unauthorized(self):
        with self.client as c:
            # test POST response, invalid credentials
            resp = c.post('/login', data = {'username':'wrong_user', 'password':"testuser"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn(f"Invalid credentials",html)

        pass

    def test_users(self):
        '''Can we view all users'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # Test GET without search
            resp = c.get('/users')
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("card-contents", html)
            # make sure stop-following is an option for logged in users
            self.assertIn("/users/stop-following/", html)
            # make sure follow is an option fol logged in users
            self.assertIn('/users/follow/', html)
            self.assertIn('card-bio', html)

            # Test GET with valid search
            resp = c.get('/users?username=testuser2')
            self.assertEqual(resp.status_code,200)
            html = resp.get_data(as_text=True)
            self.assertIn(f'/users/stop-following/{self.user2_id}', html)

            # Test GET with invalid search
            resp = c.get('/users?q=username=fake_username')
            self.assertEqual(resp.status_code,200)
            html = resp.get_data(as_text=True)
            self.assertNotIn('/users/follow/', html)
            self.assertIn('Sorry, no users found', html)
        pass


    def test_user(self):
        '''Can we view a user's page properly'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # test GET 
            resp = c.get(f'/users/{self.testuser.id}')
            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn(f"/users/{self.testuser.id}",html)
            self.assertIn(f'src="{self.testuser.image_url}"', html
            )
            # check to see if you can view delete options if you're the correct user
            self.assertIn(f'/users/delete', html)

            resp = c.get(f'/users/{self.user2_id}')
            html = resp.get_data(as_text=True)

            # should not be able to view the delete option of another user
            self.assertNotIn(f'/users/delete', html)
            self.assertIn("Unfollow", html)

            resp = c.get(f'/users/{self.user3_id}')
            html = resp.get_data(as_text=True)
            self.assertIn("Follow", html)

            # trying to access invalid user
            resp = c.get(f'/users/-1')
            self.assertEqual(resp.status_code, 404)

        pass 

    def test_user_following(self):
        '''Can we view following'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            # test GET behavior of users own following page
            resp = c.get(f"/users/{self.testuser.id}/following")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'src="{self.testuser.image_url}"', html)
            self.assertIn('/users/delete', html)

            # test GET behavior of another users following page, 
            # which the current user is following
            resp = c.get(f"/users/{self.user2_id}/following")
            html = resp.get_data(as_text=True)
            self.assertNotIn('/users/delete', html)
            
            # test GET behavior of another users following page,
            # who isn't following any users
            resp = c.get(f"/users/{self.user3_id}/following")
            html = resp.get_data(as_text=True)
            self.assertNotIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)
            self.assertNotIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertNotIn('/users/delete', html)

            # test invalid user
            resp = c.get(f"/users/-1/following")
            self.assertEqual(resp.status_code, 404)

        pass 

    def test_user_following_unauthorized(self):
        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)
        pass

    def test_user_followers(self):
        '''Can we show list of followers'''
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/users/{self.testuser.id}/followers")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'src="{self.testuser.image_url}"', html)
            self.assertIn('/users/delete', html)

            # test GET behavior of another users following page, 
            # which the current user is following
            resp = c.get(f"/users/{self.user2_id}/followers")
            html = resp.get_data(as_text=True)
            self.assertNotIn('/users/delete', html)
            
            # test GET behavior of another users following page,
            # who isn't following any users
            resp = c.get(f"/users/{self.user3_id}/followers")
            html = resp.get_data(as_text=True)
            self.assertNotIn('<button class="btn btn-outline-primary btn-sm">Follow</button>', html)
            self.assertNotIn('<button class="btn btn-primary btn-sm">Unfollow</button>', html)
            self.assertNotIn('/users/delete', html)

            # test invalid user
            resp = c.get(f"/users/-1/following")
            self.assertEqual(resp.status_code, 404)
        pass 
    def test_user_followers_unauthorized(self):
        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)
        pass
    def test_post_follow(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f'/users/follow/{self.user3_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('/users/delete',html)

            # test for trying to follow an invalid user
            resp = c.post(f'/users/follow/-1')
            self.assertEqual(resp.status_code, 404)
        pass 
    def test_post_follow_unauthorized(self):
        with self.client as c:
            resp = c.post(f'/users/follow/{self.user3_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            pass

    def test_stop_following(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f'/users/stop-following/{self.user2_id}')
            self.assertEqual(resp.status_code, 302)


        pass 
    def test_stop_following_unauthorized(self):
        with self.client as c:
            resp = c.post(f'/users/stop-following/{self.user2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            pass

    def test_user_profile(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/users/profile')
            html = resp.get_data(as_text=True)
            self.assertIn('<form method="POST" id="user_form">', html)
            self.assertIn('<button class="btn btn-success">Edit this user!</button>', html)

            #test updating user
            resp = c.post('/users/profile', 
                data={"username":"updated_test_user",
                "email":"test-email@email.com",
                "password":"testuser",
                "header_image_url": None,
                "bio":None,
                "image_url":None}, follow_redirects= True   )
            user = User.query.get(self.testuser.id)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(user.username, 'updated_test_user')

            # test updating user with incorrect password
            resp = c.post('/users/profile', 
                data={"username":"updated_test_user",
                "email":"test-email@email.com",
                "password":"incorrect_password",
                "header_image_url": None,
                "bio":None,
                "image_url":None}, 
                follow_redirects=True)
            
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Incorrect password.",html)
        pass 

    def test_user_profile_unauthorized(self):
        with self.client as c:
            resp = c.get(f'/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            pass

    def test_user_delete(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            id = self.testuser.id
            resp = c.post('/users/delete')
            self.assertEqual(resp.status_code, 302)
            resp = c.get(f'/users/{id}')
            self.assertEqual(resp.status_code, 404)

        pass 

    def test_user_delete_unauthorized(self):
        with self.client as c:
            resp = c.post(f'/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", html)
            pass

    








    


