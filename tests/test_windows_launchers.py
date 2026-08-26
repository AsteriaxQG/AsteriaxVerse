from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = [ROOT / "LANCER.bat", ROOT / "CONSTRUIRE_EXE.bat"]


class WindowsLauncherTests(unittest.TestCase):
    def test_launchers_are_ascii_with_strict_crlf(self) -> None:
        for path in LAUNCHERS:
            with self.subTest(path=path.name):
                data = path.read_bytes()
                self.assertTrue(data)
                self.assertTrue(all(byte < 128 for byte in data))
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
                self.assertGreater(data.count(b"\r\n"), 0)
                self.assertEqual(data.count(b"\n"), data.count(b"\r\n"))
                self.assertEqual(data.count(b"\r"), data.count(b"\r\n"))
                self.assertTrue(data.endswith(b"\r\n"))

    def test_every_goto_target_exists(self) -> None:
        for path in LAUNCHERS:
            with self.subTest(path=path.name):
                text = path.read_bytes().decode("ascii")
                labels = {
                    match.group(1).casefold()
                    for match in re.finditer(r"^:([A-Za-z0-9_]+)\r?$", text, re.MULTILINE)
                }
                targets = {
                    match.group(1).casefold()
                    for match in re.finditer(r"\bgoto\s+([A-Za-z0-9_]+)", text, re.IGNORECASE)
                }
                self.assertEqual(targets - labels, set())
                self.assertEqual(text.count("("), text.count(")"))


if __name__ == "__main__":
    unittest.main()

