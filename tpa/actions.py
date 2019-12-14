import collections
import re
from typing import Callable, List
import app


class RegexActionParser:
    """Call a registered function when an action is received.

    First, the user calls @register_action to register actions that should be taken when
    a regex is matched. Then, the user can call @take_action with a given command. The command
    will be checked against the registered regexes, calling one or more callbacks (see the
    @single_action flag in @take_action).
    """

    def __init__(self):
        self._registry = collections.OrderedDict()

    def register_regex(
        self,
        regex: str,
        action: Callable[..., None],
        type_conversion_functions: List[Callable] = None,
        help_msg="",
    ):
        """Register a regex with a callable.

        This allows the callable to be invoked when the regex is matched in a call to
        @take_action.
        """
        self._registry[re.compile(regex)] = (
            action,
            type_conversion_functions,
            help_msg,
        )

    def take_action(self, command: str, single_action: bool = False):
        """Check whether @command matches a registered regex, and call one or more corresponding
        registered callbacks."""
        for (
            regex,
            (action, type_conversion_functions, _),
        ) in self._registry.items():
            match_group = regex.match(command)
            if match_group is not None:
                args = match_group.groups()
                if type_conversion_functions is not None:
                    assert len(args) == len(
                        type_conversion_functions
                    ), "Not enough type conversion functions (expected {}, got {})".format(
                        len(args), len(type_conversion_functions)
                    )
                    args = [
                        t(a) for t, a in zip(type_conversion_functions, args)
                    ]
                action(*args)

                if single_action:
                    break

    def is_valid_regex(self, command: str) -> bool:
        """Check whether the command matches at least one registered regex."""
        for regex in self._registry:
            match_group = regex.match(command)
            if match_group is not None:
                return True
        return False

    def get_help(self) -> str:
        """Return a help string."""
        ret = "Commands:\n"
        help_msgs = [
            "{}: {}".format(regex.pattern, help_msg)
            for regex, (_, _, help_msg) in self._registry.items()
        ]
        ret += "\n\t".join(help_msgs)
        return ret


class RegexActions:
    """This abstract class contains a bunch of class methods that register callbacks on a
    @RegexActionParser.

    Its only real current purpose is organization (keeping all the registered actions and
    callbacks next to each other. It could be easily replaced by a pile of free functions.
    """

    @classmethod
    def register_orange_button_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def orange_button_action():
            print("Received orange button action")
            server.privmsg(channel_name, "ORANGE BUTTON ACTION")
            app.mouse.take_orange_action()

        parser.register_regex(
            "^o$", orange_button_action, help_msg="click the orange button"
        )

    @classmethod
    def register_blue_button_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def blue_button_action():
            print("Received blue button action")
            server.privmsg(channel_name, "BLUE BUTTON ACTION")
            app.mouse.take_blue_action()

        parser.register_regex(
            "^b$", blue_button_action, help_msg="click the blue button"
        )

    @classmethod
    def register_nth_selection_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def nth_selection_action(n: int):
            print("Received nth selection action")
            server.privmsg(channel_name, "SELECT ELEMENT {} ACTION".format(n))
            app.mouse.play_card(n, 7)

        parser.register_regex(
            "^([0-9])+$",
            nth_selection_action,
            type_conversion_functions=[int],
            help_msg="select the nth element",
        )

    @classmethod
    def register_block_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def block_action(*args):
            print(args)
            assert len(args) % 2 == 0  # Map from blockers to attackers.
            blocker_spec = [int(a) for a in args]

            blocker_string = "; ".join(
                [
                    "{} -> {}".format(a, b)
                    for a, b in zip(blocker_spec[::2], blocker_spec[1::2])
                ]
            )
            print("Received blocker action")
            server.privmsg(channel_name, "BLOCK {}".format(blocker_string))

        single_block_regex = r"([0-9]+):([0-9]+);"
        blocker_regex = "^{sbr}+$".format(sbr=single_block_regex)

        parser.register_regex(
            blocker_regex, block_action, help_msg="specify blocker mapping"
        )

    @classmethod
    def register_attack_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def attack_action(*args):
            assert len(args) % 2 == 0
            print("Received attacker action")
            server.privmsg(channel_name, "ATTACK {}".format(args))

        single_attack_regex = r"([0-9]+):([a-zA-Z0-9_, ]+);"
        attacker_regex = "^{sar}+$".format(sar=single_attack_regex)

        parser.register_regex(
            attacker_regex, attack_action, help_msg="specify attacker mapping"
        )

    @classmethod
    def register_named_permanent_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def named_permanent_action(identifier):
            print("Received named permanent action")
            server.privmsg(
                channel_name, "NAMED PERMANENT {}".format(identifier)
            )

        parser.register_regex(
            "^([a-zA-Z0-9_, ]+:[0-9])+$",
            named_permanent_action,
            help_msg="select a permanent",
        )

    @classmethod
    def register_player_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def player_action(identifier):
            print("Received player action")
            server.privmsg(channel_name, "PLAYER {}".format(identifier))

        parser.register_regex(
            "^(you|me)$", player_action, help_msg="Select a player"
        )


def make_parser(server, channel_name):
    parser = RegexActionParser()

    RegexActions.register_orange_button_action(parser, server, channel_name)
    RegexActions.register_blue_button_action(parser, server, channel_name)
    RegexActions.register_nth_selection_action(parser, server, channel_name)
    RegexActions.register_block_action(parser, server, channel_name)
    RegexActions.register_attack_action(parser, server, channel_name)
    RegexActions.register_named_permanent_action(parser, server, channel_name)
    RegexActions.register_player_action(parser, server, channel_name)

    return parser
