from pymongo import MongoClient
import os
import datetime

col = MongoClient(os.environ['mongo_host'], int(os.environ['mongo_port']))['metrics']['app_metrics']

from flask import Flask
app = Flask(__name__)

@app.route('/metrics')
def hello_world():
    result = ''
    for record in col.find():
        last_modified = record['last_modified']
        time_differ = (datetime.datetime.utcnow() - last_modified).seconds
        if time_differ <= 2:
            result += record['key'] + ' ' + record['value'] + '\n'
    return result

if __name__ == "__main__":
    app.run(host='0.0.0.0')
