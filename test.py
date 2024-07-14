from flask import Flask, make_response
import gzip
import zlib

app = Flask(__name__)

@app.route("/")
def hello_world():
    # response = make_response(gzip.compress("abc".encode()))
    # # print(gzip.decompress(gzip.compress("abc".encode())))
    # response.headers.set('Content-Type', 'text/plain')
    # response.headers.set('Content-Length', len())
    return zlib.compress("abc".encode())