import actions
import irc
import irc.client
import irc.connection
import irc.events
import configparser
import ssl
from collections import defaultdict, Counter, OrderedDict
import re

"""
TODO: add randomization for tiebreaking
"""


class ArenaVoteCounter:
    """This class is responsible for tallying and interpreting votes."""

    QUORUM_SIZE = 2

    def __init__(self):
        self._votes = defaultdict(int)
        self.reset_votes()

    def vote(self, vote: str) -> bool:
        self._votes[vote] += 1

    def tally_votes(self) -> str:
        return Counter(self._votes).most_common(1)[0][0]

    def reset_votes(self) -> None:
        self._votes.clear()
        # Add an explicit key. This will be the default "tally_votes" action.
        self._votes["pass"] = 0

    def check_quorum(self) -> bool:
        return sum(self._votes.values()) >= self.QUORUM_SIZE


"""
        _named_permanent_regex = 

        _player_regex = "^(you|me)$"

        RegexActions.register_orange_button_action(self._parser)

        self._parser.register_regex(
            _orange_regex,
            orange_button_action,
            help_msg="click the orange button",
        )
        self._parser.register_regex(
            _blue_regex, blue_button_action, help_msg="click the blue button"
        )
        self._parser.register_regex(
            _n_regex,
            nth_element_action,
            help_msg="select the nth available option",
        )
        self._parser.register_regex(
            _blocker_regex,
            _blocker_action,
            help_msg="map blockers to attackers",
        )
        self._parser.register_regex(
            _attacker_regex,
            _attacker_action,
            help_msg="map attackers to opponents/planeswalkers",
        )
        # TODO I guess this needs to work on planeswalkers the opponent controls, and that I control. (Shocking my vs. their planeswalker).
        self._parser.register_regex(
            _named_permanent_regex,
            _named_permanent_action,
            help_msg="select a permanent on the battlefield",
        )

"""


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

    def on_chat_command(self, msg):
        print("received message {}".format(msg))

        if msg == "p":
            self.server.privmsg(self._channel_name, "Initiating Voting")
            self._votes = ArenaVoteCounter()
            return

        if msg == "h":
            commands_msg = self._parser.get_help()
            commands_msg = commands_msg.replace("\n", "    ")
            commands_msg = commands_msg.replace("\t", "  ")
            self.server.privmsg(self._channel_name, commands_msg)
            return

        if msg == "x":
            self.choose_action()
            return

        if self._parser.is_valid_regex(msg):
            self._votes.vote(msg)

        if self._votes.check_quorum():
            self.choose_action()

    def choose_action(self) -> None:
        """Choose a vote action, and reset the votes counter."""
        action = self._votes.tally_votes()
        self._parser.take_action(action, single_action=True)
        self._votes.reset_votes()


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
