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
    def register_primary_button_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def primary_button_action():
            print("Received primary button action")
            server.privmsg(channel_name, "PRIMARY BUTTON ACTION")
            # The primary button is in the lower position.
            app.mouse.take_lower_action()

        parser.register_regex(
            "^p$", primary_button_action, help_msg="click the primary (single) button"
        )

    @classmethod
    def register_upper_lower_button_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def upper_lower_button_action(tag):
            print("Received upper/lower button action")
            server.privmsg(channel_name, "UPPER/LOWER BUTTON ACTION")
            if tag == 'u':
                app.mouse.take_upper_action()
            elif tag == 'l':
                app.mouse.take_lower_action()

        parser.register_regex(
            "^(u|l)$", upper_lower_button_action, help_msg="click the upper or lower of two buttons"
        )

    @classmethod
    def register_play_ith_of_n_cards_in_hand_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def play_ith_of_n_cards_in_hand_action(i: int, n: int):
            print("Received play ith of n card in hand action")
            server.privmsg(channel_name, "PLAY CARD {} of {} IN HAND ACTION".format(i, n))
            app.mouse.play_card(i, n)

        parser.register_regex(
            "^p([0-9])+,([0-9])+$",
            play_ith_of_n_cards_in_hand_action,
            type_conversion_functions=[int, int],
            help_msg="play the ith of n cards in hand",
        )

    @classmethod
    def register_click_ith_of_n_cards_in_hand_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def click_ith_of_n_cards_in_hand_action(i: int, n: int):
            print("Received click ith of n card in hand action")
            server.privmsg(channel_name, "CLICK CARD {} of {} IN HAND ACTION".format(i, n))
            app.mouse.click_a_card(i, n)

        parser.register_regex(
            "^c([0-9])+,([0-9])+$",
            click_ith_of_n_cards_in_hand_action,
            type_conversion_functions=[int, int],
            help_msg="click the ith of n cards in hand",
        )

    @classmethod
    def register_click_nth_card_in_hand_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def click_nth_card_in_hand_action(n: int):
            print("Received click nth card in hand action")
            server.privmsg(channel_name, "CLICK CARD {} IN HAND ACTION".format(n))
            hand_size = app.mtga_app.mtga_watch_app.game.hero.hand.total_count
            app.mouse.click_a_card(n, hand_size)

        parser.register_regex(
            "^c([0-9])+$",
            click_nth_card_in_hand_action,
            type_conversion_functions=[int],
            help_msg="click the nth card in hand",
        )

    @classmethod
    def register_play_nth_card_in_hand_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def play_nth_card_in_hand_action(n: int):
            print("Received play nth card in hand action")
            server.privmsg(channel_name, "PLAY CARD {} IN HAND ACTION".format(n))
            hand_size = app.mtga_app.mtga_watch_app.game.hero.hand.total_count
            import logging
            logging.warn('playing card {} of {} cards in hand.'.format(n, hand_size))
            app.mouse.play_card(n, hand_size)

        parser.register_regex(
            "^p([0-9])+$",
            play_nth_card_in_hand_action,
            type_conversion_functions=[int],
            help_msg="play the nth card in hand",
        )

    @classmethod
    def register_click_our_nth_creature_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def click_our_nth_creature_action(i: int, n: int):
            print("Received click our nth creature action")
            server.privmsg(channel_name, "CLICK OUR {}/{} CREATURE ACTION".format(i, n))
            app.mouse.click_our_nth_creature(i, n)

        parser.register_regex(
            "^coc([0-9])+,([0-9])+$",
            click_our_nth_creature_action,
            type_conversion_functions=[int, int],
            help_msg="click our nth creature",
        )

    @classmethod
    def register_click_their_nth_creature_action(
        cls, parser:RegexActionParser, server, channel_name
    ):
        def click_their_nth_creature_action(i: int, n: int):
            print("Received click their nth creature action")
            server.privmsg(channel_name, "CLICK THEIR {}/{} CREATURE ACTION".format(i, n))
            app.mouse.click_their_nth_creature(i, n)

        parser.register_regex(
            "^ctc([0-9])+,([0-9])+$",
            click_their_nth_creature_action,
            type_conversion_functions=[int, int],
            help_msg="click their nth creature",
        )

    @classmethod
    def register_click_player_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def click_player_action(identifier):
            print("Received click player action")
            server.privmsg(channel_name, "CLICK PLAYER {}".format(identifier))
            app.mouse.click_player(identifier)

        parser.register_regex(
            "^(you|me)$", click_player_action, help_msg="click a player"
        )

    @classmethod
    def register_accept_modal_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def accept_modal_action(i: int, n: int):
            print("Received accept modal action")
            server.privmsg(channel_name, "ACCEPT MODAL ACTION {} OF {}".format(i, n))
            app.mouse.accept_modal_action(i, n)

        parser.register_regex(
            "^am([0-9])+,([0-9])+$",
            accept_modal_action,
            type_conversion_functions=[int, int],
            help_msg="accept a modal action (such as shockland prompt)",
        )

    @classmethod
    def register_choose_modal_action(
        cls, parser: RegexActionParser, server, channel_name
    ):
        def choose_model_action(i: int, n: int):
            print("Received choose modal action")
            server.privmsg(channel_name, "CHOOSE MODAL ACTION {} OF {}".format(i, n))
            app.mouse.choose_modal_action(i, n)

        parser.register_regex(
            "^cm([0-9])+,([0-9])+$",
            choose_model_action,
            type_conversion_functions=[int, int],
            help_msg="choose a modal action (such as a planeswalker ability)",
        )

    @classmethod
    def register_choose_click_action(
        cls, parser:RegexActionParser, server, channel_name
    ):
        def choose_click_action(x: int, y: int):
            # TODO we may need to convert from floats to pixel coordinates on the screen.
            print("Received choose click action, at coordinates ({}, {})".format(x, y))
            server.privmsg(channel_name, "CHOOSE CLICK ACTION AT ({}, {})".format(x, y))
            app.mouse.click(x, y)

        parser.register_regex(
            "^CLICK ([0-9])+,([0-9])+$",
            choose_click_action,
            type_conversion_functions=[int, int],
            help_msg="click at pixels (x, y)",
        )



def make_parser(server, channel_name):
    parser = RegexActionParser()

    RegexActions.register_primary_button_action(parser, server, channel_name)
    RegexActions.register_upper_lower_button_action(parser, server, channel_name)
    RegexActions.register_click_nth_card_in_hand_action(parser, server, channel_name)
    RegexActions.register_click_ith_of_n_cards_in_hand_action(parser, server, channel_name)
    RegexActions.register_play_nth_card_in_hand_action(parser, server, channel_name)
    RegexActions.register_play_ith_of_n_cards_in_hand_action(parser, server, channel_name)
    RegexActions.register_click_our_nth_creature_action(parser, server, channel_name)
    RegexActions.register_click_their_nth_creature_action(parser, server, channel_name)
    RegexActions.register_click_player_action(parser, server, channel_name)
    RegexActions.register_accept_modal_action(parser, server, channel_name)
    RegexActions.register_choose_modal_action(parser, server, channel_name)
    RegexActions.register_choose_click_action(parser, server, channel_name)

    return parser
