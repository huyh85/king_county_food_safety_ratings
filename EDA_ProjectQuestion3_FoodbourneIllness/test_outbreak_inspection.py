"""
Tony Hang, Jaiden Poon, Amy Li
CSE 163 A

A file that contains CSE 163 Project Exploration
Data Unit Test for the King County's Public
Health Safety - Foodborne Outbreak
"""

import unittest
import pandas as pd

from outbreak_inspection import clean_address


class TestCleanAddress(unittest.TestCase):
    """Tests for the clean_address function."""

    def test_standard_address(self):
        result = clean_address("123 Main St.")
        self.assertEqual(result, "123 MAIN ST")

    def test_lowercase_address(self):
        result = clean_address("123 main street")
        self.assertEqual(result, "123 MAIN STREET")

    def test_extra_whitespace(self):
        result = clean_address("  123   Main   St  ")
        self.assertEqual(result, "123 MAIN ST")

    def test_punctuation(self):
        result = clean_address("123 Main St., Apt #4")
        self.assertEqual(result, "123 MAIN ST APT 4")

    def test_missing_value(self):
        self.assertEqual(clean_address(None), "")
        self.assertEqual(clean_address(float("nan")), "")

    def test_empty_string(self):
        self.assertEqual(clean_address(""), "")


if __name__ == "__main__":
    unittest.main()
