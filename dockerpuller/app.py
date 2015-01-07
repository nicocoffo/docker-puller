from flask import Flask
from flask import request
from flask import jsonify
import json
import subprocess
import requests

app = Flask(__name__)
config = None

@app.route('/', methods=['POST'])
def hook_listen():
    # Verify token 
    if request.args.get('token') == config['token']:
        hook = request.args.get('hook')
        data = request.json
        callback = None

        # Get callback url and container name, if no hook was provided
        if request.json:
            callback = data.get('callback_url')
            if not hook and data.get('repository'):
                hook = data['repository'].get('name')

        # Call hook, if it exists
        if hook:
            hook_value = config['hooks'].get(hook)
            if hook_value:
                try:
                    subprocess.call(hook_value)
                    complete_callback(callback, 'success')
                    return jsonify(success=True), 200
                except OSError as e:
                    complete_callback(callback, 'failure')
                    return jsonify(success=False, error=str(e)), 400
            else:
                complete_callback(callback, 'error')
                return jsonify(success=False, error="Hook not found"), 404
        else:
            complete_callback(callback, 'error')
            return jsonify(success=False, error="Invalid request: missing hook"), 400
    else:
        return jsonify(success=False, error="Invalid token"), 400

def complete_callback(callback, result):
    if callback:
        requests.post(callback, data=json.dumps({'state':result}))

def load_config():
    with open('config.json') as config_file:    
        return json.load(config_file)

if __name__ == '__main__':
    config = load_config()
    app.run(host=config.get('host', 'localhost'), port=config.get('port', 8000))
