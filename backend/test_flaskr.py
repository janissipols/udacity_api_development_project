import os
import unittest
import json
from sqlalchemy import text

from app import create_app
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
            # Add a sample category and question for testing
            category = Category(type='Test Category')
            db.session.add(category)
            db.session.commit()
            question = Question(question='Test Question', answer='Test Answer', category=category.id, difficulty=1)
            db.session.add(question)
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

    def test_get_paginated_questions(self):
        """Test GET for paginated questions."""
        print("\n--- Testing GET /questions ---")
        res = self.client.get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['questions'])
        self.assertGreater(data['total_questions'], 0)
        print("    - GET /questions: Passed")

    def test_404_if_page_does_not_exist(self):
        """Test 404 for non-existent page."""
        print("\n--- Testing GET /questions?page=1000 ---")
        res = self.client.get('/questions?page=1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        print("    - GET /questions?page=1000 (404): Passed")

    def test_delete_question(self):
        """Test DELETE for a single question."""
        print("\n--- Testing DELETE /questions/<id> ---")
        # Create a question to delete
        question = Question(question='Question to delete', answer='Answer', category=1, difficulty=1)
        with self.app.app_context():
            question.insert()
            question_id = question.id

        res = self.client.delete(f'/questions/{question_id}')
        data = json.loads(res.data)

        # Check that the question was deleted
        with self.app.app_context():
            deleted_question = Question.query.filter(Question.id == question_id).one_or_none()

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)
        self.assertIsNone(deleted_question)
        print("    - DELETE /questions/<id>: Passed")

    def test_404_if_question_to_delete_does_not_exist(self):
        """Test 404 for deleting a non-existent question."""
        print("\n--- Testing DELETE /questions/1000 (404) ---")
        res = self.client.delete('/questions/1000')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        print("    - DELETE /questions/1000 (404): Passed")


if __name__ == "__main__":
    unittest.main()
