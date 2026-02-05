from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    CORS(app) # Initialize CORS here

    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    # Use the after_request decorator to set Access-Control-Allow headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        formatted_categories = {category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'categories': formatted_categories
        })

    @app.route('/questions')
    def get_questions():
        page = request.args.get('page', 1, type=int)

        pagination = Question.query.order_by(Question.id).paginate(page=page, per_page=QUESTIONS_PER_PAGE, error_out=False)
        paginated_questions = [question.format() for question in pagination.items]

        if not paginated_questions:
            abort(404)

        categories = Category.query.all()
        formatted_categories = {category.id: category.type for category in categories}

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': pagination.total,
            'current_page': pagination.page,
            'total_pages': pagination.pages,
            'categories': formatted_categories,
            'current_category': None
        })
        
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        if not all([new_question, new_answer, new_category, new_difficulty]):
            abort(422)

        try:
            question = Question(question=new_question, answer=new_answer,
                                category=new_category, difficulty=new_difficulty)
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id
            })

        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route('/questions/category', methods=['POST'])
    def get_questions_by_category():
        body = request.get_json()
        category_id = body.get('category_id', None)

        if not category_id:
            abort(400) # Bad request if no category_id is provided

        try:
            # Check if category exists
            category = Category.query.filter_by(id=category_id).one_or_none()
            if category is None:
                abort(404) # Category not found

            selection = Question.query.filter_by(category=category_id).order_by(Question.id)
            total_questions = selection.count()

            page = request.args.get('page', 1, type=int)
            pagination = selection.paginate(page=page, per_page=QUESTIONS_PER_PAGE, error_out=False)
            paginated_questions = [question.format() for question in pagination.items]

            if not paginated_questions:
                abort(404)

            return jsonify({
                'success': True,
                'questions': paginated_questions,
                'total_questions': total_questions,
                'current_category': category.type
            })
        except:
            abort(422) # Unprocessable entity for other errors

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    return app

