from flask import Flask, jsonify, request
from azure.cosmos import CosmosClient
import uuid
from collections import defaultdict

app = Flask(__name__)

# Cosmos DB config
COSMOS_DB_URI = 'https://moorhouseassessment2.documents.azure.com:443/'
COSMOS_DB_KEY = 'J96F3DjCf6ds63Kuv0z2RPKYWBlNbC6xVNqMHRphWbKXWG6FWpQSdLrgpQ6lnzieyvK2Q1CDebpKACDbU0HMZw=='
COSMOS_DB_DATABASE = 'MMADB'
QUESTIONS_CONTAINER = 'Phase1Questions'
RESPONSES_CONTAINER = 'Phase1Responses'

client = CosmosClient(COSMOS_DB_URI, credential=COSMOS_DB_KEY)
database = client.get_database_client(COSMOS_DB_DATABASE)

questions_container = database.get_container_client(QUESTIONS_CONTAINER)
responses_container = database.get_container_client(RESPONSES_CONTAINER)

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

@app.route('/submit-responses', methods=['POST'])
def submit_responses():
    try:
        data = request.get_json()
        session_id = data.get("sessionId")
        responses = data.get("responses")
        
        # Create a response item to be stored in the database
        response_item = {
            "id": str(uuid.uuid4()),  # Generate a new UUID for the response item
            "sessionId": session_id,
            "responses": responses
        }
        
        # Store the response item in the database
        responses_container.create_item(body=response_item)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        app.logger.error(f"Error submitting responses: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
