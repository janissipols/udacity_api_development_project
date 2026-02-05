import os
import unittest
import json
from sqlalchemy import text
from dotenv import load_dotenv
from app import create_app
from models import db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        
        load_dotenv(dotenv_path='./backend/.env.test')

        self.database_name = os.getenv('DB_NAME')
        self.database_user = os.getenv('DB_USER')
        self.database_password = os.getenv('DB_PASSWORD')
        self.database_host = os.getenv('DB_HOST')
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
        """Test GET for categories and verify against database."""
        print("\n--- Testing GET /categories ---")
        res = self.client.get('/categories')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)

        with self.app.app_context():
            categories_from_db = Category.query.all()
            formatted_categories_from_db = {str(category.id): category.type for category in categories_from_db}
            self.assertEqual(data['categories'], formatted_categories_from_db)
        print("    - GET /categories: Passed")

    def test_get_paginated_questions(self):
        """Test GET for paginated questions and verify against database."""
        print("\n--- Testing GET /questions ---")
        res = self.client.get('/questions')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        
        with self.app.app_context():
            total_questions_in_db = Question.query.count()
            self.assertEqual(data['total_questions'], total_questions_in_db)

            # Verify the content of the first question
            first_question_from_api = data['questions'][0]
            first_question_from_db = db.session.get(Question, first_question_from_api['id'])
            self.assertIsNotNone(first_question_from_db)
            self.assertEqual(first_question_from_api['question'], first_question_from_db.question)
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
        """Test DELETE for a single question and verify persistence."""
        print("\n--- Testing DELETE /questions/<id> ---")
        # Create a question to delete
        with self.app.app_context():
            question = Question(question='Question to delete', answer='Answer', category=1, difficulty=1)
            question.insert()
            question_id = question.id

        res = self.client.delete(f'/questions/{question_id}')
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertEqual(data['deleted'], question_id)

        # Verify the question is no longer in the database
        with self.app.app_context():
            deleted_question = db.session.get(Question, question_id)
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

    def test_create_question(self):
        """Test POST to create a new question and verify persistence."""
        print("\n--- Testing POST /questions ---")
        new_question_data = {
            'question': 'What is the capital of Argentina?',
            'answer': 'Buenos Aires',
            'category': 1,
            'difficulty': 2
        }
        res = self.client.post('/questions', json=new_question_data)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['created'])

        # Verify the question was persisted correctly
        with self.app.app_context():
            created_question = db.session.get(Question, data['created'])
            self.assertIsNotNone(created_question)
            self.assertEqual(created_question.question, new_question_data['question'])
            self.assertEqual(created_question.answer, new_question_data['answer'])
        print("    - POST /questions: Passed")

    def test_422_if_question_creation_fails(self):
        """Test 422 for failing to create a new question."""
        print("\n--- Testing POST /questions (422) ---")
        new_question = {
            'question': 'This question is missing an answer',
            'category': 1,
            'difficulty': 2
        }
        res = self.client.post('/questions', json=new_question)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 422)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'unprocessable')
        print("    - POST /questions (422): Passed")

    def test_search_questions(self):
        """Test POST to search for questions."""
        print("\n--- Testing POST /questions/search ---")
        search = {'searchTerm': 'Test'}
        res = self.client.post('/questions/search', json=search)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertIsNotNone(data['questions'])
        self.assertGreater(data['total_questions'], 0)
        print("    - POST /questions/search: Passed")

    def test_404_if_search_term_is_not_provided(self):
        """Test 404 for searching without a search term."""
        print("\n--- Testing POST /questions/search (404) ---")
        search = {'searchTerm': ''}
        res = self.client.post('/questions/search', json=search)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'resource not found')
        print("    - POST /questions/search (404): Passed")

    def test_get_questions_by_category(self):
        """Test POST to get questions by category."""
        print("\n--- Testing POST /questions/category ---")
        res = self.client.post('/questions/category', json={'category_id': 1})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertIsNotNone(data['questions'])
        self.assertGreater(data['total_questions'], 0)
        self.assertIsNotNone(data['current_category'])
        print("    - POST /questions/category: Passed")

    def test_400_if_category_id_is_not_provided(self):
        """Test 400 for getting questions without a category ID."""
        print("\n--- Testing POST /questions/category (400) ---")
        res = self.client.post('/questions/category', json={})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        print("    - POST /questions/category (400): Passed")

    def test_play_quiz(self):
        """Test POST to play the quiz."""
        print("\n--- Testing POST /quizzes ---")
        quiz_round = {
            'previous_questions': [],
            'quiz_category': {'id': 1, 'type': 'Test Category'}
        }
        res = self.client.post('/quizzes', json=quiz_round)
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['success'], True)
        self.assertTrue(data['question'])
        print("    - POST /quizzes: Passed")

    def test_400_if_quiz_fails(self):
        """Test 400 for failing to play the quiz."""
        print("\n--- Testing POST /quizzes (400) ---")
        res = self.client.post('/quizzes', json={})
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], 'bad request')
        print("    - POST /quizzes (400): Passed")


if __name__ == "__main__":
    unittest.main()
