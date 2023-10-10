from flask import Flask, jsonify, request
from flask_cors import CORS
import uuid

app = Flask(__name__)

# Enable CORS for specific origins (for production and development)
CORS(app, resources={r"/*": {"origins": ["https://brave-coast-00c913710.3.azurestaticapps.net"]}})

@app.route('/start-session', methods=['POST'])
def start_session():
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Optionally: Store session_id and additional data in a database
    # ...

    # Send the session ID back to the frontend
    return jsonify({"sessionId": session_id})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
