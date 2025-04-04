import os
from flask import Flask, request, jsonify
import requests
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Available tools and resources
tools = {
    'add': {
        'id': 'add',
        'description': 'Add two numbers',
        'execute': lambda params: {'result': int(params['a']) + int(params['b'])}
    },
}

# TOOLS
@app.route('/tools', methods=['GET'])
def list_tools():
    return jsonify({'tools': list(tools.values())})

@app.route('/tools/<tool_id>', methods=['POST'])
def use_tool(tool_id):
    if tool_id not in tools:
        return jsonify({'error': 'Tool not found'}), 404
    return jsonify(tools[tool_id]['execute'](request.json))

# curl -X POST http://localhost:3030/tools/add -H "Content-Type: application/json" -d '{"a": 2, "b": 3}'

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3030))
    print(f"SLOP API running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)