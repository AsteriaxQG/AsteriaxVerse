from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import Mock, patch

from core.updater import (
    APPLY_UPDATE_FLAG,
    apply_downloaded_update,
    check_app_update,
    consume_update_result,
    download_app_update,
    launch_app_update,
    run_update_bootstrap,
    version_key,
)


OFFICIAL_EXE_URL = "https://raw.githubusercontent.com/AsteriaxQG/AsteriaxVerse/main/AsteriaxVerse.exe"


class FakeResponse:
    def __init__(self, payload: bytes, url: str):
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


class UpdaterTests(unittest.TestCase):
    def test_version_comparison(self) -> None:
        self.assertGreater(version_key("v1.3.10"), version_key("1.3.9"))

    def test_manifest_requires_integrity_data_for_new_release(self) -> None:
        payload = json.dumps({"version": "1.4.1", "download_url": OFFICIAL_EXE_URL}).encode()
        with patch("core.updater.urllib.request.urlopen", return_value=FakeResponse(payload, "https://example.test/manifest.json")):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                check_app_update("https://example.test/manifest.json")

    def test_manifest_accepts_verified_new_release(self) -> None:
        checksum = "a" * 64
        payload = json.dumps(
            {
                "version": "1.4.1",
                "download_url": OFFICIAL_EXE_URL,
                "sha256": checksum,
                "size": 12345,
                "release_notes": "Test",
            }
        ).encode()
        with patch("core.updater.urllib.request.urlopen", return_value=FakeResponse(payload, "https://example.test/manifest.json")):
            result = check_app_update("https://example.test/manifest.json")
        self.assertTrue(result["available"])
        self.assertEqual(result["sha256"], checksum)
        self.assertEqual(result["size"], 12345)

    def test_manifest_request_bypasses_stale_caches(self) -> None:
        payload = json.dumps({"version": "1.3.5"}).encode()
        captured: list[urllib.request.Request] = []

        def open_request(request: urllib.request.Request, timeout: int = 0) -> FakeResponse:
            captured.append(request)
            return FakeResponse(payload, request.full_url)

        with patch("core.updater.urllib.request.urlopen", side_effect=open_request):
            result = check_app_update("https://example.test/manifest.json")
        self.assertFalse(result["available"])
        self.assertIn("asteriax_cache=", captured[0].full_url)
        self.assertEqual(captured[0].get_header("Cache-control"), "no-cache")

    def test_download_is_kept_only_after_size_hash_and_pe_checks(self) -> None:
        payload = b"MZ" + (b"Asteriax" * 2048)
        checksum = hashlib.sha256(payload).hexdigest()
        info = {
            "latest_version": "1.3.6",
            "download_url": OFFICIAL_EXE_URL,
            "sha256": checksum,
            "size": len(payload),
        }
        progress: list[float] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch("core.updater.can_self_update", return_value=True),
                patch("core.updater.user_data_dir", return_value=root),
                patch("core.updater.urllib.request.urlopen", return_value=FakeResponse(payload, OFFICIAL_EXE_URL)),
            ):
                result = download_app_update(info, lambda fraction, _message: progress.append(fraction))
            self.assertEqual(result.read_bytes(), payload)
            self.assertEqual(result.name, "AsteriaxVerse-1.3.6.exe")
            self.assertEqual(progress[-1], 1.0)

    def test_corrupt_download_is_deleted(self) -> None:
        payload = b"MZcorrupt"
        info = {
            "latest_version": "1.3.6",
            "download_url": OFFICIAL_EXE_URL,
            "sha256": "0" * 64,
            "size": len(payload),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch("core.updater.can_self_update", return_value=True),
                patch("core.updater.user_data_dir", return_value=root),
                patch("core.updater.urllib.request.urlopen", return_value=FakeResponse(payload, OFFICIAL_EXE_URL)),
            ):
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    download_app_update(info)
            update_dir = root / "updates"
            self.assertFalse(any(update_dir.glob("*.part")))
            self.assertFalse(any(update_dir.glob("*.exe")))

    def test_integrated_updater_replaces_and_relaunches_target(self) -> None:
        new_payload = b"MZnew-version" * 256
        old_payload = b"MZold-version" * 128
        checksum = hashlib.sha256(new_payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "AsteriaxVerse-1.3.6.exe"
            target = root / "AsteriaxVerse.exe"
            log = root / "update.log"
            source.write_bytes(new_payload)
            target.write_bytes(old_payload)
            launched = Mock(pid=777)
            with (
                patch("core.updater._process_exists", return_value=False),
                patch("core.updater.subprocess.Popen", return_value=launched) as popen,
            ):
                installed = apply_downloaded_update(source, target, checksum, 4242, log)
            self.assertEqual(installed, target)
            self.assertEqual(target.read_bytes(), new_payload)
            self.assertFalse(target.with_name(target.name + ".old").exists())
            popen.assert_called_once()
            self.assertIn("Version installée et relancée", log.read_text(encoding="utf-8"))
            result_path = root / "update_result.json"
            result = consume_update_result(result_path)
            self.assertIsNotNone(result)
            self.assertEqual(result["version"], "1.4.0")
            self.assertFalse(result_path.exists())

    def test_launcher_starts_downloaded_exe_without_powershell(self) -> None:
        payload = b"MZintegrated-updater" * 128
        checksum = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "AsteriaxVerse-1.3.6.exe"
            target = root / "AsteriaxVerse.exe"
            source.write_bytes(payload)
            target.write_bytes(b"MZold")
            launched = Mock(pid=888)
            with (
                patch("core.updater.can_self_update", return_value=True),
                patch("core.updater.sys.executable", str(target)),
                patch("core.updater.user_data_dir", return_value=root),
                patch("core.updater.subprocess.Popen", return_value=launched) as popen,
            ):
                log = launch_app_update(source, {"sha256": checksum})
            command = popen.call_args.args[0]
            self.assertEqual(command[0], str(source))
            self.assertEqual(command[1], APPLY_UPDATE_FLAG)
            self.assertNotIn("powershell.exe", command)
            self.assertTrue(log.exists())

    def test_bootstrap_restores_old_exe_when_relaunch_fails(self) -> None:
        new_payload = b"MZnew-version" * 256
        old_payload = b"MZold-version" * 128
        checksum = hashlib.sha256(new_payload).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "AsteriaxVerse-1.3.6.exe"
            target = root / "AsteriaxVerse.exe"
            log = root / "update.log"
            source.write_bytes(new_payload)
            target.write_bytes(old_payload)
            with (
                patch("core.updater.sys.executable", str(source)),
                patch("core.updater._process_exists", return_value=False),
                patch(
                    "core.updater.subprocess.Popen",
                    side_effect=[OSError("relaunch failed"), Mock(pid=999)],
                ),
            ):
                result = run_update_bootstrap(
                    [APPLY_UPDATE_FLAG, str(target), checksum, "4242", str(log)]
                )
            self.assertEqual(result, 1)
            self.assertEqual(target.read_bytes(), old_payload)
            self.assertIn("Ancienne version restaurée", log.read_text(encoding="utf-8"))
            self.assertFalse((root / "update_result.json").exists())


if __name__ == "__main__":
    unittest.main()
