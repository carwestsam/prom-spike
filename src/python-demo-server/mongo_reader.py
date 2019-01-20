from pymongo import MongoClient
import os

col = MongoClient(os.environ['mongo_host'], int(os.environ['mongo_port']))['info']['app_info']

from flask import Flask
app = Flask(__name__)

@app.route('/metrics')
def hello_world():
    result = ''
    for record in col.find():
        result += record['key'] + ' ' + record['value'] + '\n'
    return result
