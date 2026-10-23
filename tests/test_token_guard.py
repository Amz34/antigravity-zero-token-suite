import json
import tempfile
import unittest
from pathlib import Path

from scripts.token_guard import estimate_file_metrics, format_report, main, scan_workspace_tokens


class TokenGuardTests(unittest.TestCase):
    def test_estimate_file_metrics_counts_lines_and_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "sample.py"
            sample.write_text("print('hello')\nprint('world')\n", encoding="utf-8")
            metrics = estimate_file_metrics(sample, chars_per_token=4)
            self.assertEqual(metrics["lines"], 2)
            self.assertEqual(metrics["chars"], 30)
            self.assertEqual(metrics["est_tokens"], 7)

    def test_scan_workspace_flags_files_above_max_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            small = root / "small.py"
            small.write_text("x = 1\n" * 10, encoding="utf-8")

            large = root / "large.md"
            large.write_text("line_content_1234\n" * 200, encoding="utf-8")

            ignored_dir = root / "node_modules"
            ignored_dir.mkdir()
            (ignored_dir / "bundle.js").write_text("a = 1;\n" * 500, encoding="utf-8")

            summary = scan_workspace_tokens(root, max_lines=150)
            self.assertEqual(summary["total_files"], 2)
            self.assertEqual(len(summary["heavy_files"]), 1)
            self.assertEqual(summary["heavy_files"][0]["path"], "large.md")
            self.assertEqual(summary["heavy_files"][0]["lines"], 200)

    def test_format_report_and_strict_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "oversized.py").write_text("pass\n" * 30, encoding="utf-8")
            summary = scan_workspace_tokens(root, max_lines=20)
            report = format_report(summary)
            self.assertIn("[ALERT]", report)
            self.assertIn("oversized.py", report)
            self.assertEqual(main([str(root), "--max-lines", "20", "--strict", "--json"]), 1)
            self.assertEqual(main([str(root), "--max-lines", "50", "--strict", "--json"]), 0)


if __name__ == "__main__":
    unittest.main()
