from flask import Flask, jsonify, request
import uuid

app = Flask(__name__)

@app.route('/start-session', methods=['POST'])
def start_session():
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Optionally: Store session_id and additional data in a database
        # ...

        # Send the session ID back to the frontend
        return jsonify({"sessionId": session_id}), 201  # 201 Created

    except Exception as e:
        app.logger.error(f"Error creating session: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500  # 500 Internal Server Error

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)