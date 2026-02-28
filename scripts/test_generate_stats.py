#!/usr/bin/env python3
"""Tests for generate_stats.py language exclusion logic."""

import unittest
from unittest.mock import patch

from generate_stats import fetch_language_stats, EXCLUDE_LANGS


class TestFetchLanguageStats(unittest.TestCase):
    """Tests for fetch_language_stats function."""

    def _make_repo(self, name, language, fork=False):
        return {
            "name": name,
            "language": language,
            "fork": fork,
            "languages_url": f"https://api.github.com/repos/user/{name}/languages",
        }

    @patch("generate_stats.api_request")
    def test_excludes_jupyter_notebook_language_key(self, mock_api):
        """Jupyter Notebook bytes should be excluded from language stats."""
        repos = [self._make_repo("my-repo", "Python")]
        mock_api.return_value = {
            "Python": 5000,
            "Jupyter Notebook": 50000,
        }
        result = fetch_language_stats(repos)
        lang_names = [name for name, _ in result]
        self.assertNotIn("Jupyter Notebook", lang_names)
        self.assertIn("Python", lang_names)

    @patch("generate_stats.api_request")
    def test_skips_repos_with_jupyter_notebook_primary_language(self, mock_api):
        """Repos whose primary language is Jupyter Notebook should be skipped entirely."""
        repos = [
            self._make_repo("notebook-repo", "Jupyter Notebook"),
            self._make_repo("python-repo", "Python"),
        ]

        def side_effect(url):
            if "notebook-repo" in url:
                return {"Jupyter Notebook": 80000, "Python": 20000}
            if "python-repo" in url:
                return {"Python": 10000}
            return {}

        mock_api.side_effect = side_effect
        result = fetch_language_stats(repos)
        lang_names = [name for name, _ in result]
        self.assertNotIn("Jupyter Notebook", lang_names)
        # Python should only come from python-repo, not notebook-repo
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "Python")
        self.assertAlmostEqual(result[0][1], 100.0)

    @patch("generate_stats.api_request")
    def test_skips_forked_repos(self, mock_api):
        """Forked repos should be skipped."""
        repos = [self._make_repo("forked", "Python", fork=True)]
        mock_api.return_value = {"Python": 5000}
        result = fetch_language_stats(repos)
        self.assertEqual(result, [])
        mock_api.assert_not_called()

    @patch("generate_stats.api_request")
    def test_normal_languages_included(self, mock_api):
        """Non-excluded languages should be included normally."""
        repos = [self._make_repo("web-app", "TypeScript")]
        mock_api.return_value = {"TypeScript": 30000, "JavaScript": 10000, "CSS": 5000}
        result = fetch_language_stats(repos)
        lang_names = [name for name, _ in result]
        self.assertIn("TypeScript", lang_names)
        self.assertIn("JavaScript", lang_names)
        self.assertIn("CSS", lang_names)

    def test_jupyter_notebook_in_exclude_langs(self):
        """Verify Jupyter Notebook is in EXCLUDE_LANGS."""
        self.assertIn("Jupyter Notebook", EXCLUDE_LANGS)


if __name__ == "__main__":
    unittest.main()
