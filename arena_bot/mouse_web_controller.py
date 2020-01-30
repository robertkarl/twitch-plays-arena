__author__ = "Maxwell Horton <maxwell.christian.horton@gmail.com>"

import argparse
import logging
import urllib.request
import sys
import time

import requests
import sklearn.cluster
import scipy.stats
import ctypes

import sched
import time

MAX_READ_SIZE = 10 ** 7

MOUSEEVENTF_MOVE = 0x0001  # mouse move
MOUSEEVENTF_LEFTDOWN = 0x0002  # left button down
MOUSEEVENTF_LEFTUP = 0x0004  # left button up
MOUSEEVENTF_RIGHTDOWN = 0x0008  # right button down
MOUSEEVENTF_RIGHTUP = 0x0010  # right button up
MOUSEEVENTF_MIDDLEDOWN = 0x0020  # middle button down
MOUSEEVENTF_MIDDLEUP = 0x0040  # middle button up
MOUSEEVENTF_WHEEL = 0x0800  # wheel button rolled
MOUSEEVENTF_ABSOLUTE = 0x8000  # absolute move

_SCHEDULER = sched.scheduler(time.time, time.sleep)

def click(x, y):
    # type: (int, int) -> None
    ctypes.windll.user32.SetCursorPos(x, y)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)  # left down
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)  # left up

def click_with_delay(x, y, seconds=0):
    _SCHEDULER.enter(seconds, 1, click, argument=(x, y))
    _SCHEDULER.run()

class ArenaVoteCounter:
    """This class is responsible for tallying and interpreting votes."""
    def __init__(self, quorum_size):
        self.quorum_size = quorum_size
        self._votes = []

    def register_votes(self, vote) -> bool:
        """Accept votes in the form [[x1, y1], [x2, y2], ...]"""
        self._votes.extend(vote)

    def reset(self):
        self._votes = []

    def should_act(self):
        return len(self._votes) > self.quorum_size

    def tally_vote(self):
        if self._votes == []:
            return [0, 0]

        # Do k-means clustering with 5 means, then choose an element from the most popular cluster.
        print("Tallying votes by clustering")
        kmeans = sklearn.cluster.KMeans(n_clusters=min(5, len(self._votes)))
        kmeans.fit(self._votes)

        # Find the largest cluster by label.
        mode = scipy.stats.mode(kmeans.labels_)[0][0]
        # Get the position of that cluster.
        center = kmeans.cluster_centers_[mode]

        x, y = int(center[0]), int(center[1])

        return [x, y]

def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", type=str, help="url to connect to for requesting votes")
    parser.add_argument("--loop_sleep", type=float, help="sleep time in the main loop")
    parser.add_argument("--quorum_size", type=int, help="quorum size for tallying votes")
    return parser.parse_args()

def get_info_over_http(url):
    """Sends an HTTP request to the given url, and tries to extract votes.

    Arguments:
        url: an endpoint to query.
    
    Returns:
        a list [[x1, y1], [x2, y2], ...] of votes.
    """
    logging.info("Sending HTTP Request to {}".format(url))
    data = requests.get(url)
    if data.status_code == requests.codes.ok:
        return data.json()
    else:
        print("error: received http code {!r}, in message: {}".format(data.status_code, data))
        return []

def main_loop(url, loop_sleep, quorum_size):
    vote_counter = ArenaVoteCounter(quorum_size)
    while True:
        logging.info("Requesting a new vote")
        new_votes = get_info_over_http(url)
        vote_counter.register_votes(new_votes)

        if vote_counter.should_act():
            logging.info("Processing votes")
            highest_vote = vote_counter.tally_vote()
            logging.info("Chose coordinates: {}".format(highest_vote))
            click(*highest_vote)
            vote_counter.reset()

        time.sleep(loop_sleep)


def main(argv):
    logging.basicConfig(level=logging.INFO)
    args = parse_args(argv)
    main_loop(args.url, args.loop_sleep, args.quorum_size)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
