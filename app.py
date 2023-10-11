from flask import Flask, jsonify, request, send_from_directory
from azure.cosmos import CosmosClient
import uuid
from collections import defaultdict
import os

app = Flask(__name__, static_folder='survey-app/build')

# Cosmos DB config
COSMOS_DB_URI = 'https://moorhouseassessment2.documents.azure.com:443/'
COSMOS_DB_KEY = 'J96F3DjCf6ds63Kuv0z2RPKYWBlNbC6xVNqMHRphWbKXWG6FWpQSdLrgpQ6lnzieyvK2Q1CDebpKACDbU0HMZw=='
COSMOS_DB_DATABASE = 'MMADB'
QUESTIONS_CONTAINER = 'Phase1Questions'
RESPONSES_CONTAINER = 'Phase1Responses'
ROLES_CONTAINER = 'Roles'
REGISTERED_USERS_CONTAINER = 'RegisteredUsers'  # Added this line

client = CosmosClient(COSMOS_DB_URI, credential=COSMOS_DB_KEY)
database = client.get_database_client(COSMOS_DB_DATABASE)

questions_container = database.get_container_client(QUESTIONS_CONTAINER)
responses_container = database.get_container_client(RESPONSES_CONTAINER)
roles_container = database.get_container_client(ROLES_CONTAINER)
users_container = database.get_container_client(REGISTERED_USERS_CONTAINER)

@app.route('/start-session', methods=['POST'])
def start_session():
    try:
        session_id = str(uuid.uuid4())
        return jsonify({"sessionId": session_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating session: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/get-questions', methods=['GET'])
def get_questions():
    try:
        questions_query = "SELECT * FROM c"
        questions = list(questions_container.query_items(query=questions_query, enable_cross_partition_query=True))
        
        grouped_questions = defaultdict(list)

        for question in questions:
            theme = question.get("theme", "")
            grouped_questions[theme].append({
                "id": question["id"],
                "text": question["text"],
                "phase": question.get("phase", "")
            })

        formatted_questions = [
            {"theme": theme, "questions": qs} for theme, qs in grouped_questions.items()
        ]

        return jsonify({"questions": formatted_questions})
    except Exception as e:
        app.logger.error(f"Error fetching questions: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/get-roles', methods=['GET'])
def get_roles():
    try:
        roles_query = "SELECT * FROM c"
        queried_roles = list(roles_container.query_items(query=roles_query, enable_cross_partition_query=True))
        
        # Extract 'title' from each role entry
        role_titles = [role['title'] for role in queried_roles]

        return jsonify({"roles": role_titles})
    except Exception as e:
        app.logger.error(f"Error fetching roles: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/submit-responses', methods=['POST'])
def submit_responses():
    try:
        data = request.get_json()
        session_id = data.get("sessionId")
        responses = data.get("responses")
        
        response_item = {
            "id": str(uuid.uuid4()),
            "sessionId": session_id,
            "responses": responses
        }
        
        responses_container.create_item(body=response_item)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        app.logger.error(f"Error submitting responses: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500
        
@app.route('/register-user', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        role = data.get("role")
        session_id = data.get("sessionId")
        
        new_user = {
            "id": str(uuid.uuid4()),  # Generate a new UUID for the user
            "name": name,
            "email": email,
            "role": role,
            "sessionId": session_id
        }
        
        # Add the new user to the RegisteredUsers container
        users_container.create_item(body=new_user)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        app.logger.error(f"Error registering user: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

# Additional code:

def calculate_averages(responses):
    theme_totals = {}
    theme_counts = {}

    for response in responses:
        for _, question_response in response["responses"].items():
            theme = question_response["theme"]
            score = question_response["score"]

            if theme not in theme_totals:
                theme_totals[theme] = 0
                theme_counts[theme] = 0

            theme_totals[theme] += score
            theme_counts[theme] += 1

    averages = []
    for theme, total in theme_totals.items():
        average = total / theme_counts[theme]
        averages.append({"theme": theme, "averageScore": average})

    return averages

@app.route('/get-averages', methods=['POST'])
def get_averages():
    try:
        data = request.get_json()
        session_id = data.get("sessionId")

        responses_query = f"SELECT * FROM c WHERE c.sessionId = '{session_id}'"
        responses = list(responses_container.query_items(query=responses_query, enable_cross_partition_query=True))

        averages = calculate_averages(responses)

        return jsonify({"scores": averages})
    except Exception as e:
        app.logger.error(f"Error fetching averages: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
