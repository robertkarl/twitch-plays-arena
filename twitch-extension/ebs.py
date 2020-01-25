"""
FLASK_ENV=development FLASK_APP=ebs flask run
curl -X POST 'localhost:5000/vote?x=5&y=10&id=1'
curl -X POST 'localhost:5000/vote?x=10&y=10&id=1'
curl 'localhost:5000/vote'
"""
import datetime
import queue
import flask
import sys
import collections

app = flask.Flask(__name__)
q = queue.Queue()

rl = collections.defaultdict(lambda: datetime.datetime(2000, 1, 1))
MIN_INTERVAL = datetime.timedelta(seconds=3)


@app.route('/vote', methods=["get", "post"])
def vote():
    if flask.request.method == 'GET':
        try:
            x, y = q.get(block=False)
        except queue.Empty:
            return ""
        return "{}, {}".format(x, y)
    else:
        if not flask.request.method == 'POST':
            flask.abort(500)
        now = datetime.datetime.now()
        r = flask.request
        uid = r.values['id']
        last = rl[uid]
        if now  - last < MIN_INTERVAL:
            return ('NOPE', 500)
        coordx = flask.request.values['x']
        coordy = flask.request.values['y']
        rl[uid] = now
        q.put((coordx, coordy))
        return ('OK', 200)



