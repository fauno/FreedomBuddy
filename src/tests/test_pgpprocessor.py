#! /usr/bin/env python # -*- mode: auto-fill; fill-column: 80 -*-

"""Tests for the PGP Processing Tools.

All aspects of each PGP processor should be fully tested: this verifies
identity, allowing trust to exist in the system.  If this is mucked up, trust
isn't verifiable.

"""

import gnupg
import pgpprocessor
import unittest
import utilities

def remove_line(string, line, preserve_newlines = True):
    """Remove a line from a multi-line string."""

    if preserve_newlines and not line.endswith("\n"):
        line += "\n"

    return str(string.splitlines(preserve_newlines).remove(line))


class MessageWrapper(unittest.TestCase):
    """Basic setup for message-signing tests.

    These tests would run much faster if I could use setUpClass (>30x faster:
    signing three messages for each test consumes lots of entropy that needs to
    be rebuilt?), but that's a Python 2.7 feature.  I'll rewrite this when
    Debian Stable includes Python 2.7 or Python 3.X.  It's much prettier.

    """
    def setUp(self):

        self.iterations = 3
        self.gpg = gnupg.GPG(gnupghome='../data/test_gpg_home')
	config = utilities.load_config()
    	self.key_id = utilities.safe_load(config, "pgpprocessor", "keyid", 0)
        self.messages = utilities.multi_sign(
            gpg = self.gpg,
            iterations = self.iterations,
	    keyid = self.key_id)

class UnwrapperTest(MessageWrapper):
    """Verify that we can unwrap multiply-signed PGP messages correctly."""

    def setUp(self):
        super(UnwrapperTest, self).setUp()

        self.unwrapper = pgpprocessor.Unwrapper(self.messages[-1],
                                                self.gpg)

    def test_messages_wrapped(self):
        """Were the messages correctly wrapped in the first place?"""

        self.assertEqual(self.iterations + 1, len(self.messages))

    def test_unwrap_all_messages(self):
        """Do we unwrap the right number of messages?"""

        # count each element in the iterator once, skipping the first.
        self.assertEqual(self.iterations, sum([1 for e in self.unwrapper]))

    def test_dont_uwrap(self):
        """Creating an unwrapper shouldn't unwrap the message.

        Only iterating through the unwrapper should unwrap it.  We don't want to
        process the message at all until we're explicitly told to do so.

        """
        self.assertEqual(self.unwrapper.message, self.messages[-1])
        self.assertEqual(str(self.unwrapper).strip(), "")

    def test_iterator_unwraps_correctly(self):
        """The iterator should correctly unwrap each stage of the message."""
        unwrapped_messages = self.messages[:-1]

        for message in reversed(unwrapped_messages):
            self.unwrapper.next()
            self.assertEqual(message.strip(), self.unwrapper.message.strip())

    def test_no_header_invalid(self):
        """Messages without heads are considered invalid."""

        self.unwrapper.message = remove_line(
            self.unwrapper.message, "-----BEGIN PGP SIGNED MESSAGE-----\n")

        self.assertRaises(StopIteration, self.unwrapper.next)

    def test_no_body_invalid(self):
        """Messages without bodies are considered invalid."""

        self.unwrapper.message = remove_line(self.unwrapper.message, "\n")

        self.assertRaises(StopIteration, self.unwrapper.next)

    def test_no_footer_invalid(self):
        """Messages without feet are considered invalid."""

        self.unwrapper.message = remove_line(
            self.unwrapper.message, "-----BEGIN PGP SIGNATURE-----\n")

        self.assertRaises(StopIteration, self.unwrapper.next)

    def test_no_end_invalid(self):
        """Messages without tails are considered invalid."""

        self.unwrapper.message = remove_line(
            self.unwrapper.message, "-----END PGP SIGNATURE-----\n")

        self.assertRaises(StopIteration, self.unwrapper.next)


if __name__ == "__main__":
    unittest.main()
