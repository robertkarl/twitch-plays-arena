import actions
import irc
import irc.client
import irc.connection
import irc.events
import configparser
import ssl
from collections import defaultdict, Counter, OrderedDict
import re
import pathlib
import threading
import logging
import sklearn.cluster
import scipy
logging.basicConfig(level=logging.WARN)

"""
TODO: add randomization for tiebreaking
"""

_TPA_HANDLER = None

def _run_client_forever(handler):
    handler.reactor.process_forever()
    print('done running forever')

def get_tpa_handler():
    # type: (None) -> TpaEventHandler
    """Get the chat bot, creating it if not available."""
    global _TPA_HANDLER
    if _TPA_HANDLER is None:
        config = get_config(pathlib.Path.home() / "config.ini")
        _TPA_HANDLER = get_tpa_handler_and_client(config["main"])["tpa_handler"]
        reactor_run_thread = threading.Thread(target=_run_client_forever, args=(_TPA_HANDLER,))
        _TPA_HANDLER._running_thread = reactor_run_thread
        reactor_run_thread.start()
    return _TPA_HANDLER


class ArenaVoteCounter:
    """This class is responsible for tallying and interpreting votes."""

    QUORUM_SIZE = 1

    def __init__(self):
        self._votes = []
        self.reset_votes()

    def vote(self, vote: str) -> bool:
        # Vote must be a string of the form "CLICK x,y"
        assert vote.startswith("CLICK ")
        x_comma_y = vote.split()[1]
        x, y = x_comma_y.split(",")
        print("Got x={}, y={}".format(x, y))

        self._votes.append([int(x), int(y)])

    def tally_votes(self) -> str:
        if self._votes is None:
            return ""

        if len(self._votes) == 0:
            return "CLICK 0,0"

        # Do k-means clustering with 5 means, then choose an element from the most popular cluster.
        print("Tallying votes by clustering")
        kmeans = sklearn.cluster.KMeans(n_clusters=min(5, len(self._votes)))
        kmeans.fit(self._votes)

        # Find the largest cluster by label.
        mode = scipy.stats.mode(kmeans.labels_)[0][0]
        # Get the position of that cluster.
        center = kmeans.cluster_centers_[mode]

        x, y = int(center[0]), int(center[1])

        return "CLICK {},{}".format(x,y)

    def start_counting(self) -> None:
        self._votes = []

    def reset_votes(self) -> None:
        self._votes = [] # TODO might want to change this

    def check_quorum(self) -> bool:
        return len(self._votes) >= self.QUORUM_SIZE

    def is_tallying(self):
        return self._votes is not None

    def done_tallying(self) -> bool:
        # TODO add a timer here.
        return self.check_quorum()


class TpaEventHandler:
    """
    Our event handler.
    Stores the reactor and server instances (irc library objects) for later use. """

    def __init__(self, reactor, server, channel_to_join):
        # type: (irc.client.server) -> None
        self.server = server
        self.reactor = reactor
        self._has_requested_perms = False
        self._channel_name = channel_to_join
        self._votes = ArenaVoteCounter()
        self._votes.start_counting() # TODO probably should remove this.
        self._parser = actions.make_parser(server, self._channel_name)

    def on_welcome(self, connection, event):
        self.request_only_once()

    def on_cap(self, connection, event):
        self.server.join(self._channel_name)

    def on_pong(self, connection, event):
        self.server.ping("tmi.twitch.tv")

    def request_only_once(self):
        """
        Request permissions once.
        :return:
        """
        if self._has_requested_perms:
            return
        else:
            print("requesting permissions")
            self.server.cap("LS")
            self.server.cap(
                "REQ",
                "twitch.tv/commands",
                "twitch.tv/tags",
                "twitch.tv/membership",
            )
            self.server.cap("END")
            self._has_requested_perms = True

    def on_userstate(self, connection, event):
        print(event)

    def on_clearchat(self, connection, event):
        print(event)

    def on_anyevent(self, connection, event):
        """
        pretty much a catch-all event handler.
        """
        print(event)

    def on_pubmsg(self, connection, event):
        self.on_chat_command(event.arguments[0])
    def send_message_from_bot(self, msg):
        self.server.privmsg(self._channel_name, msg)

    def on_chat_command(self, msg):
        print("received message {}".format(msg))

        if msg == "prompt":
            self.server.privmsg(self._channel_name, "Initiating Voting")
            self._votes = ArenaVoteCounter()
            return

        if msg == "help":
            self.server.privmsg(self._channel_name, "Click the overlay to vote on an action.")
            return

        if msg == "execute":
            self.choose_action()
            return

        if self._parser.is_valid_regex(msg):
            self._votes.vote(msg)

    def choose_action(self) -> None:
        """Choose a vote action, and reset the votes counter."""
        action = self._votes.tally_votes()

        if action == "":
            self.server.privmsg(self._channel_name, "NO VOTES RECEIVED")
        else:
            self._parser.take_action(action, single_action=True)
        self._votes.reset_votes()

    def get_vote_counter(self):
        return self._votes


def main(config):
    client = get_tpa_handler_and_client(config)["client"]
    client.process_forever()

def get_tpa_handler_and_client(config):
    server_addr = config["server"]
    port = int(config["port"])
    creds = config["creds"]
    channel_name = config["channel"]

    ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)

    client = irc.client.Reactor()
    for event_type in irc.events.numeric.values():

        def cb(connection, event):
            print(event)

        client.add_global_handler(event_type, cb)
    server = client.server()
    server.connect(
        server=server_addr,
        port=port,
        nickname="arena__bot",
        password=creds,
        connect_factory=ssl_factory,
    )
    tpa_handler = TpaEventHandler(client, server, channel_name)
    client.add_global_handler("welcome", tpa_handler.on_welcome)
    # The following is for users joining the channel:
    # client.add_global_handler("join", tpa_handler.on_anyevent)
    client.add_global_handler("userstate", tpa_handler.on_userstate)
    client.add_global_handler("clearchat", tpa_handler.on_clearchat)
    client.add_global_handler("roomstate", tpa_handler.on_anyevent)
    client.add_global_handler("cap", tpa_handler.on_cap)
    client.add_global_handler("pubmsg", tpa_handler.on_pubmsg)

    return {"tpa_handler": tpa_handler, "client": client}

def get_config(pathname: pathlib.Path):
    config = configparser.ConfigParser()
    config.read(pathname)
    return config

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.WARN)
    config = get_config("tpa.ini")

    main(config["main"])
