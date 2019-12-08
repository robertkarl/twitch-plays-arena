import irc
import irc.client
import irc.connection
import irc.events
import configparser
import ssl
from collections import defaultdict, Counter
import re


class ArenaVoteCounter:
    QUORUM_SIZE = 2

    def __init__(self):
        self._votes = defaultdict(int)
        # Add an explicit key. This will be the default "tally_votes" action.
        self._votes["pass"] = 0

    def pass_turn(self):
        self._votes["pass"] += 1

    def play_card(self, index):
        self._votes["card{}".format(index)] += 1

    def attack(self):
        self._votes["attack"] += 1

    def tally_votes(self):
        return Counter(self._votes).most_common(1)[0]

    def accept(self):
        self._votes["accept"] += 1

    def cancel(self):
        self._votes["cancel"] += 1

    def check_quorum(self):
        return sum(self._votes.values()) >= self.QUORUM_SIZE


HELP_MESSAGE = "Commands: p=priority, x=execute, #1-9=play card 1-9, a=all attack, >>=pass, h=help "
"c=accept, k=cancel"


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
                "REQ", "twitch.tv/commands", "twitch.tv/tags", "twitch.tv/membership",
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

    def on_chat_command(self, msg):
        if msg == "p":
            self._votes = ArenaVoteCounter()
            self.server.privmsg(
                self._channel_name, "We have priority. {}".format(HELP_MESSAGE)
            )
            # Start a timer to count the votes.
            return

        if msg == "h":
            self.server.privmsg(self._channel_name, HELP_MESSAGE)
            return

        if getattr(self, "_votes", None) is None:
            print("Invalid command {}".format(msg))
            return

        if msg == "x":
            self.choose_action()
            return
        elif msg == ">>":
            self._votes.pass_turn()
        elif msg == "a":
            self._votes.attack()
        elif re.match("([1-9])", msg):
            # Play the nth card in your hand.
            n = int(re.match("([0-9])", msg).group(1))
            self._votes.play_card(n)
        elif msg == "c":
            self._votes.accept()
        elif msg == "k":
            self._votes.cancel()

        if self._votes.check_quorum():
            self.choose_action()

    def choose_action(self) -> None:
        """Choose a vote action, and reset the votes counter."""
        action = self._votes.tally_votes()
        print(action)
        action_name, action_count = action
        self.server.privmsg(
            self._channel_name, "{} with {} votes".format(action_name, action_count),
        )
        self._votes = None


def main(config):
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
        nickname="rskjr",
        password=creds,
        connect_factory=ssl_factory,
    )
    print(server.get_server_name())

    tpa_handler = TpaEventHandler(client, server, channel_name)
    client.add_global_handler("welcome", tpa_handler.on_welcome)
    # The following is for users joining the channel:
    # client.add_global_handler("join", tpa_handler.on_anyevent)
    client.add_global_handler("userstate", tpa_handler.on_userstate)
    client.add_global_handler("clearchat", tpa_handler.on_clearchat)
    client.add_global_handler("roomstate", tpa_handler.on_anyevent)
    client.add_global_handler("cap", tpa_handler.on_cap)
    client.add_global_handler("pubmsg", tpa_handler.on_pubmsg)

    client.process_forever()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.WARN)
    config = configparser.ConfigParser()
    config.read("tpa.ini")

    main(config["main"])
