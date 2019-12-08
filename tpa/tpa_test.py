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


if __name__ == "__main__":
    unittest.main()
