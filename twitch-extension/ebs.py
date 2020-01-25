"""
Allow users to 'vote' for a click. Store their responses and rate limit them.

Effectively this is a queue that stores tuples.


FLASK_ENV=development FLASK_APP=ebs flask run
curl -X POST 'localhost:5000/vote?x=5&y=10&id=1'
curl -X POST 'localhost:5000/vote?x=10&y=10&id=1'
curl 'localhost:5000/vote'
"""
import datetime
import queue
import flask
import sys
import json
import collections

app = flask.Flask(__name__)
q = queue.Queue()

rl = collections.defaultdict(lambda: datetime.datetime(2000, 1, 1))
MIN_INTERVAL = datetime.timedelta(seconds=3)


def empty_queue():
    ans = []
    while q.qsize():
        try:
            thing = q.get_nowait()
            print("got thing {}".format(thing))
            ans.append(thing)
        except queue.Empty:
            return ans
    return ans


@app.route("/vote", methods=["get", "post"])
def vote():
    if flask.request.method == "GET":
        return json.dumps(empty_queue())
    else:
        if not flask.request.method == "POST":
            flask.abort(500)
        now = datetime.datetime.now()
        r = flask.request
        uid = r.values["id"]
        last = rl[uid]
        if now - last < MIN_INTERVAL:
            return ("NOPE", 500)
        coordx = int(flask.request.values["x"])
        coordy = int(flask.request.values["y"])
        rl[uid] = now
        q.put((coordx, coordy))
        return ("OK", 200)
