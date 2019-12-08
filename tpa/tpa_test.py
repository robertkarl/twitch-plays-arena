import unittest
import tpa
import sys
from contextlib import contextmanager
from io import StringIO

# https://stackoverflow.com/questions/4219717/how-to-assert-output-with-nosetest-unittest-in-python
@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TPAVoteTest(unittest.TestCase):
    def setUp(self):
        self.avc = tpa.ArenaVoteCounter()
        # Fake handler with no backend.
        self.eh = tpa.TpaEventHandler(None, None, None)

    @unittest.skipUnless(False, "skipping LOL!")
    def test_vote_tallies(self):
        self.eh.on_chat_command("!priority")

        self.eh.on_chat_command("!pass")
        self.eh.on_chat_command("!play0")
        self.eh.on_chat_command("!play1")
        self.eh.on_chat_command("!play1")

        with captured_output() as (out, err):
            self.eh.on_chat_command("!execute")

        out = out.getvalue().strip()
        self.assertEqual(out, "received message !execute\n('card1', 2)")

    def test_parse_blocker_vote(self):
        self.assertTrue(tpa._parse_blocker_vote("1:2,3:4"))

        self.assertTrue(tpa._parse_attacker_vote("1:Teferi the Bro,2:you"))

        self.assertTrue(tpa._parse_named_permanent_vote("Castle Vantress"))

        self.assertTrue(tpa._parse_player_vote("you"))


if __name__ == "__main__":
    unittest.main()
