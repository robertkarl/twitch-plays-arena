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
        # Add an explicit key. This will be the default "tally_votes" action.
        self._votes["pass"] = 0

        _orange_regex = "^o$"
        _blue_regex = "^b$"
        _n_regex = "^[0-9]+$"

        single_block_regex = r"[0-9]+:[0-9]+"
        _blocker_regex = "^({sbr};)*{sbr}$".format(sbr=single_block_regex)

        single_attack_regex = r"[0-9]+:[a-zA-Z0-9_, ]+"
        _attacker_regex = "^({sar};)*{sar}$".format(sar=single_attack_regex)

        _named_permanent_regex = "^[a-zA-Z0-9_, ]+:[0-9]+$"

        _player_regex = "^(you|me)$"

        self._descriptions_to_regexes = OrderedDict(
            {
                "Click the orange button": _orange_regex,
                "Click the blue button": _blue_regex,
                "Choose the nth item": _n_regex,
                "Map blockers, e.g. 1:2 will map our first blocker to the second attacker": _blocker_regex,
                "Map attackers to entities, e.g. 1:you,3:Teferi, Time Raveler will map our first attacker to the opponent, and our third attacker to Teferi": _attacker_regex,
                "Choose a permanent to click on": _named_permanent_regex,
                "Choose a player": _player_regex,
            }
        )

    def vote(self, vote: str) -> bool:
        for regex in self._descriptions_to_regexes.values():
            if re.match(regex, vote):
                print("{} Matched regex {}".format(vote, regex))
                self._votes[vote] += 1
                return True
        print("Invalid regex {}".format(vote))
        return False

    def tally_votes(self):
        return Counter(self._votes).most_common(1)[0]

    def check_quorum(self):
        return sum(self._votes.values()) >= self.QUORUM_SIZE



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
            self.server.privmsg(self._channel_name, "Initiating Voting")
            self._votes = ArenaVoteCounter()
            return

        if msg == "h":
            commands_msg = [
                "{}: {}".format(d, r)
                for d, r in self._votes._descriptions_to_regexes.items()
            ]
            commands_msg = ",".join(commands_msg)
            self.server.privmsg(self._channel_name, commands_msg)
            return

        self._votes.vote(msg)

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
        self._votes = ArenaVoteCounter()


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
