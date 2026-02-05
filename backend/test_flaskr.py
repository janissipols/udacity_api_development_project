import os
import unittest
import json
from sqlalchemy import text

from flaskr import create_app
from models import db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.database_name = "trivia_test"
        self.database_user = "udemyuser"
        self.database_password = "udemy"
        self.database_host = "localhost:5432"
        self.database_path = f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}/{self.database_name}"

        # Create app with the test configuration
        self.app = create_app({
            "SQLALCHEMY_DATABASE_URI": self.database_path,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "TESTING": True
        })
        self.client = self.app.test_client()

        # Bind the app to the current context and create all tables
        with self.app.app_context():
            db.create_all()
            # Add a sample category for testing
            category = Category(type='Test Category')
            db.session.add(category)
            db.session.commit()

    def tearDown(self):
        """Executed after each test"""
        with self.app.app_context():
            db.session.remove()
            # Use raw SQL with CASCADE to drop tables
            db.session.execute(text("DROP TABLE IF EXISTS questions CASCADE;"))
            db.session.execute(text("DROP TABLE IF EXISTS categories CASCADE;"))
            db.session.commit()

    def test_get_categories(self):
        """Test GET for categories."""
        print("\n--- Testing GET /categories ---")
        res = self.client.get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['categories'])
        self.assertGreater(len(data['categories']), 0)
        print("    - GET /categories: Passed")


if __name__ == "__main__":
    unittest.main()
