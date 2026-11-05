"""Tests for the automatic release version calculation."""
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / 'scripts' / 'next-version.sh'


@unittest.skipIf(sys.platform == 'win32', 'the version script requires bash')
class NextVersionTests(unittest.TestCase):
    def next_version(self, current):
        result = subprocess.run(
            ['bash', str(SCRIPT), current],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def test_increments_patch(self):
        self.assertEqual(self.next_version('v2.0.8'), '2.0.9')

    def test_patch_rolls_over_to_minor(self):
        self.assertEqual(self.next_version('v2.0.9'), '2.1.0')

    def test_existing_two_digit_patch_rolls_over(self):
        self.assertEqual(self.next_version('v2.0.10'), '2.1.0')

    def test_minor_rolls_over_to_major(self):
        self.assertEqual(self.next_version('v2.9.9'), '3.0.0')


if __name__ == '__main__':
    unittest.main()
