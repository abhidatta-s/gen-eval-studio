"""Tests for gen-eval-studio. No network calls are made here."""

import csv
import json
import os
import shutil
import unittest
from unittest import mock

from gen_eval import generators, scorers
from gen_eval.pipeline import run_pipeline
from gen_eval.report import write_report
from gen_eval.templates import render_template

# Keep temp files inside the project folder (tests/_tmp), not elsewhere.
HERE = os.path.dirname(os.path.abspath(__file__))
TMP_ROOT = os.path.join(HERE, "_tmp")
SAMPLE = os.path.join(os.path.dirname(HERE), "prompts", "sample_prompts.json")


class TemplateTests(unittest.TestCase):
    def test_renders_variables(self):
        text = render_template("Hi {name}", {"name": "Sam"})
        self.assertEqual(text, "Hi Sam")

    def test_missing_variable_gives_clear_error(self):
        with self.assertRaises(ValueError) as context:
            render_template("Hi {name}", {})
        self.assertIn("name", str(context.exception))


class ScorerTests(unittest.TestCase):
    def test_max_words(self):
        self.assertTrue(scorers.check_max_words("one two", 2)[0])
        self.assertFalse(scorers.check_max_words("one two three", 2)[0])

    def test_min_words(self):
        self.assertTrue(scorers.check_min_words("one two", 2)[0])
        self.assertFalse(scorers.check_min_words("one", 2)[0])

    def test_must_include_is_case_insensitive(self):
        self.assertTrue(scorers.check_must_include("A Red LAMP", ["lamp"])[0])
        self.assertFalse(scorers.check_must_include("A red cup", ["lamp"])[0])

    def test_must_not_include(self):
        self.assertTrue(scorers.check_must_not_include("all good", ["oops"])[0])
        self.assertFalse(scorers.check_must_not_include("Oops!", ["oops"])[0])

    def test_regex(self):
        self.assertTrue(scorers.check_regex("Acme - Mug", "^[A-Za-z]+ - .+")[0])
        self.assertFalse(scorers.check_regex("Mug", "^[A-Za-z]+ - .+")[0])

    def test_no_digits(self):
        self.assertTrue(scorers.check_no_digits("twelve")[0])
        self.assertFalse(scorers.check_no_digits("12")[0])

    def test_score_needs_all_checks_to_pass(self):
        checks = [{"type": "max_words", "value": 5}, {"type": "no_digits"}]
        self.assertTrue(scorers.score("hello there", checks)["passed"])
        self.assertFalse(scorers.score("hello 2", [{"type": "no_digits"}])["passed"])

    def test_unknown_check_type(self):
        with self.assertRaises(ValueError):
            scorers.run_check({"type": "nope"}, "x")


class GeneratorTests(unittest.TestCase):
    def test_mock_is_deterministic(self):
        first = generators.mock_generate("prompt", {"a": "1"})
        second = generators.mock_generate("prompt", {"a": "1"})
        self.assertEqual(first, second)

    def test_mock_uses_variables(self):
        text = generators.mock_generate("prompt", {"product": "teapot"})
        self.assertIn("teapot", text)

    def test_hf_without_token_raises_clear_error(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(generators.GeneratorError) as context:
                generators.generate("hf", "hello", {}, None)
        self.assertIn("HF_TOKEN", str(context.exception))

    def test_unknown_generator(self):
        with self.assertRaises(generators.GeneratorError):
            generators.check_ready("banana")


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.out_dir = os.path.join(TMP_ROOT, "run")
        shutil.rmtree(TMP_ROOT, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(TMP_ROOT, ignore_errors=True)

    def test_end_to_end_mock_writes_three_files(self):
        rows = run_pipeline(SAMPLE, ["mock"], None)
        self.assertEqual(len(rows), 8)
        write_report(rows, self.out_dir)

        for name in ["results.json", "results.csv", "report.html"]:
            self.assertTrue(os.path.exists(os.path.join(self.out_dir, name)))

        with open(os.path.join(self.out_dir, "results.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data["results"]), 8)
        self.assertTrue(data["run"]["includes_mock"])

        with open(os.path.join(self.out_dir, "results.csv"), encoding="utf-8") as f:
            csv_rows = list(csv.reader(f))
        self.assertEqual(len(csv_rows), 9)  # header + 8

    def test_html_escapes_output(self):
        rows = run_pipeline(SAMPLE, ["mock"], None)
        rows[0]["output"] = "<script>alert(1)</script>"
        write_report(rows, self.out_dir)
        with open(os.path.join(self.out_dir, "report.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
