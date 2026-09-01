from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.translation_fr import (
    DEFAULT_TRANSLATION_SOURCE,
    TRANSLATION_LIVE_URL,
    TRANSLATION_SOURCES,
    find_game_installations,
    install_french_translation,
    restore_english,
    translation_status,
    validate_game_folder,
)


class FakeResponse:
    def __init__(self, payload: bytes, url: str = TRANSLATION_LIVE_URL):
        self.stream = io.BytesIO(payload)
        self.headers = {"Content-Length": str(len(payload))}
        self.url = url

    def read(self, size: int = -1) -> bytes:
        return self.stream.read(size)

    def geturl(self) -> str:
        return self.url

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        self.stream.close()


def translation_payload(suffix: str = "fr") -> bytes:
    lines = [f"item_{index}=Texte traduit {suffix} {index}" for index in range(500)]
    return ("\ufeff" + "\n".join(lines) + "\n").encode("utf-8")


class FrenchTranslationTests(unittest.TestCase):
    def _game(self, root: Path, channel: str = "LIVE") -> Path:
        game = root / "StarCitizen" / channel
        game.mkdir(parents=True)
        (game / "StarCitizen_Launcher.exe").write_bytes(b"MZ")
        return game

    def test_root_folder_resolves_to_live_and_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = self._game(root)
            self._game(root, "PTU")
            self.assertEqual(validate_game_folder(root / "StarCitizen"), live.resolve())
            self.assertEqual(find_game_installations([root / "StarCitizen"])[0], live.resolve())

    def test_install_updates_configuration_and_restores_exact_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_root = root / "asteriax-state"
            live = self._game(root)
            user_cfg = live / "user.cfg"
            original_cfg = b"r_displayInfo = 1\ng_language = english\n"
            user_cfg.write_bytes(original_cfg)
            global_ini = live / "data" / "Localization" / "french_(france)" / "global.ini"
            global_ini.parent.mkdir(parents=True)
            original_global = b"original community file"
            global_ini.write_bytes(original_global)
            progress: list[float] = []

            with patch(
                "core.translation_fr.urllib.request.urlopen",
                return_value=FakeResponse(translation_payload("v1")),
            ):
                result = install_french_translation(
                    live,
                    lambda fraction, _message: progress.append(fraction),
                    state_root=state_root,
                )

            self.assertTrue(result["installed"])
            self.assertTrue(result["managed"])
            self.assertEqual(result["source_key"], DEFAULT_TRANSLATION_SOURCE)
            self.assertEqual(result["source_label"], "Scefra")
            self.assertIn("g_language = french_(france)", user_cfg.read_text(encoding="utf-8"))
            self.assertIn("g_languageAudio = english", user_cfg.read_text(encoding="utf-8"))
            self.assertEqual(progress[-1], 1.0)

            with patch(
                "core.translation_fr.urllib.request.urlopen",
                return_value=FakeResponse(translation_payload("v2")),
            ):
                install_french_translation(live, state_root=state_root)
            self.assertIn(b"v2", global_ini.read_bytes())

            restored = restore_english(live, state_root=state_root)
            self.assertFalse(restored["installed"])
            self.assertEqual(user_cfg.read_bytes(), original_cfg)
            self.assertEqual(global_ini.read_bytes(), original_global)

    def test_fresh_install_can_return_to_english(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_root = root / "asteriax-state"
            live = self._game(root)
            with patch(
                "core.translation_fr.urllib.request.urlopen",
                return_value=FakeResponse(translation_payload()),
            ):
                install_french_translation(live, state_root=state_root)
            restore_english(live, state_root=state_root)
            self.assertFalse((live / "user.cfg").exists())
            self.assertFalse((live / "data" / "Localization" / "french_(france)" / "global.ini").exists())

    def test_rejects_untrusted_download_redirect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = self._game(root)
            response = FakeResponse(translation_payload(), "https://example.test/global.ini")
            with patch("core.translation_fr.urllib.request.urlopen", return_value=response):
                with self.assertRaisesRegex(ValueError, "source"):
                    install_french_translation(live, state_root=root / "state")

    def test_classic_translation_remains_available(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = self._game(root)
            classic_url = TRANSLATION_SOURCES["classic"]["live_url"]
            with patch(
                "core.translation_fr.urllib.request.urlopen",
                return_value=FakeResponse(translation_payload("classic"), classic_url),
            ):
                result = install_french_translation(
                    live,
                    state_root=root / "state",
                    source_key="classic",
                )
            self.assertEqual(result["source_key"], "classic")
            self.assertEqual(result["source_label"], "Circuspes classique")

    def test_status_detects_partial_manual_install(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = self._game(root)
            (live / "user.cfg").write_text("g_language = french_(france)\n", encoding="utf-8")
            status = translation_status(live, state_root=root / "state")
            self.assertFalse(status["installed"])
            self.assertTrue(status["configured"])


if __name__ == "__main__":
    unittest.main()
