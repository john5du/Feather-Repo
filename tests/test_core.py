"""核心逻辑最小测试集"""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from feather.core.config import Config, ConfigManager, MergeConfig, PathConfig, RepositoryConfig
from feather.core.json_handler import JSONHandler
from feather.core.logger import FeatherLogger
from feather.models.app import AppInfo
from feather.services.merger import AppMerger
from feather.services.updater import RepositoryUpdater
from feather.utils.formatters import ReleaseInfoExtractor
from feather.utils.validators import AppValidator, URLValidator


class VersionExtractTests(unittest.TestCase):
    def test_strips_lower_and_upper_v(self):
        self.assertEqual(ReleaseInfoExtractor.extract_version_from_tag("v1.2.3"), "1.2.3")
        self.assertEqual(ReleaseInfoExtractor.extract_version_from_tag("V1.2.5"), "1.2.5")
        self.assertEqual(ReleaseInfoExtractor.extract_version_from_tag("VV2.0"), "2.0")

    def test_strips_suffix_and_build(self):
        self.assertEqual(
            ReleaseInfoExtractor.extract_version_from_tag("v1.0.0-release"),
            "1.0.0",
        )
        self.assertEqual(
            ReleaseInfoExtractor.extract_version_from_tag("1.2.5+2"),
            "1.2.5",
        )


class IpaMatchTests(unittest.TestCase):
    def test_pattern_priority(self):
        assets = [
            {"name": "App-android.ipa", "url": "a", "size": 1},
            {"name": "App-ios.ipa", "url": "b", "size": 2},
            {"name": "App.ipa", "url": "c", "size": 3},
        ]
        matched = RepositoryUpdater._find_ipa_asset(
            assets,
            ["*ios*.ipa", "*.ipa"],
        )
        self.assertIsNotNone(matched)
        self.assertEqual(matched["name"], "App-ios.ipa")

    def test_fallback_to_second_pattern(self):
        assets = [
            {"name": "App.ipa", "url": "c", "size": 3},
        ]
        matched = RepositoryUpdater._find_ipa_asset(assets, ["*ios*.ipa", "*.ipa"])
        self.assertEqual(matched["name"], "App.ipa")

    def test_no_match_returns_none(self):
        assets = [{"name": "notes.txt", "url": "x", "size": 1}]
        self.assertIsNone(RepositoryUpdater._find_ipa_asset(assets, ["*.ipa"]))


class AppInfoRoundtripTests(unittest.TestCase):
    def test_roundtrip_preserves_extra_and_order_sensitive_fields(self):
        original = {
            "name": "Demo",
            "bundleIdentifier": "com.example.demo",
            "version": "1.0.0",
            "versionDate": "2026-01-01T00:00:00Z",
            "downloadURL": "https://example.com/app.ipa",
            "size": 10,
            "developerName": "https://github.com/demo",
            "iconURL": "https://example.com/icon.png",
            "subtitle": "demo app",
            "localizedDescription": "desc",
            "tintColor": "#ffffff",
            "versions": [
                {
                    "version": "1.0.0",
                    "date": "2026-01-01",
                    "downloadURL": "https://example.com/app.ipa",
                    "size": 10,
                    "minOSVersion": "13.0",
                    "localizedDescription": "desc",
                }
            ],
            "beta": False,
            "screenshotURLs": ["https://example.com/s.png"],
        }

        app = AppInfo.from_dict(original)
        restored = app.to_dict()

        self.assertEqual(restored["developerName"], "https://github.com/demo")
        self.assertEqual(restored["iconURL"], "https://example.com/icon.png")
        self.assertEqual(restored["beta"], False)
        self.assertEqual(restored["screenshotURLs"], ["https://example.com/s.png"])
        # 未出现的 category 不应被默认注入
        self.assertNotIn("category", restored)
        # 关键字段顺序前缀保持
        self.assertEqual(list(restored.keys())[:6], list(original.keys())[:6])

    def test_legacy_field_mapping(self):
        app = AppInfo.from_dict({
            "name": "Legacy",
            "bundleIdentifier": "com.legacy",
            "version": "1",
            "versionDate": "2026-01-01T00:00:00Z",
            "downloadURL": "https://example.com/a.ipa",
            "size": 1,
            "developer": "Dev",
            "icon": "https://example.com/i.png",
            "versions": [],
        })
        data = app.to_dict()
        self.assertEqual(data["developerName"], "Dev")
        self.assertEqual(data["iconURL"], "https://example.com/i.png")
        self.assertNotIn("developer", data)
        self.assertNotIn("icon", data)


class MergeTests(unittest.TestCase):
    def test_merge_dedup_and_orphan_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_dir = root / "app"
            app_dir.mkdir()

            source = {
                "apps": [
                    {
                        "name": "A",
                        "bundleIdentifier": "com.a",
                        "version": "2.0",
                        "versionDate": "2026-01-02T00:00:00Z",
                        "downloadURL": "https://example.com/a2.ipa",
                        "size": 20,
                        "versions": [],
                    }
                ]
            }
            (app_dir / "a.json").write_text(
                json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            all_json = {
                "name": "repo",
                "apps": [
                    {
                        "name": "A",
                        "bundleIdentifier": "com.a",
                        "version": "1.0",
                        "versionDate": "2026-01-01T00:00:00Z",
                        "downloadURL": "https://example.com/a1.ipa",
                        "size": 10,
                        "versions": [],
                    },
                    {
                        "name": "Orphan",
                        "bundleIdentifier": "com.orphan",
                        "version": "1.0",
                        "versionDate": "2026-01-01T00:00:00Z",
                        "downloadURL": "https://example.com/o.ipa",
                        "size": 1,
                        "versions": [],
                    },
                ],
            }
            all_path = root / "all.json"
            all_path.write_text(
                json.dumps(all_json, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            config = ConfigManager(
                Config(
                    paths=PathConfig(app_dir=str(app_dir), all_json=str(all_path)),
                    merge=MergeConfig(remove_orphans=True),
                )
            )
            logger = FeatherLogger.setup("ERROR")
            result = AppMerger(config, logger).merge_all()

            self.assertTrue(result.success)
            self.assertEqual(result.updated_count, 1)
            self.assertEqual(result.removed_count, 1)

            merged = json.loads(all_path.read_text(encoding="utf-8"))
            self.assertEqual(len(merged["apps"]), 1)
            self.assertEqual(merged["apps"][0]["bundleIdentifier"], "com.a")
            self.assertEqual(merged["apps"][0]["version"], "2.0")
            self.assertEqual(merged["name"], "repo")


class ValidatorAndJsonTests(unittest.TestCase):
    def test_url_and_app_validator(self):
        ok, _ = URLValidator.validate_download_url("https://x.com/a.ipa")
        self.assertTrue(ok)
        ok, err = URLValidator.validate_download_url("ftp://x")
        self.assertFalse(ok)
        self.assertIn("http", err or "")

        ok, err = AppValidator.validate_app_info({
            "name": "A",
            "bundleIdentifier": "com.a",
            "version": "1",
            "versionDate": "2026-01-01",
            "downloadURL": "https://x.com/a.ipa",
            "size": 1,
        })
        self.assertTrue(ok)

    def test_json_trailing_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.json"
            self.assertTrue(JSONHandler.save(str(path), {"a": 1}))
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertEqual(json.loads(text), {"a": 1})


class UpdateFailureSemanticsTests(unittest.TestCase):
    def test_failed_repo_marks_result_unsuccessful(self):
        config = ConfigManager(
            Config(
                repositories=[
                    RepositoryConfig(
                        name="Demo",
                        owner="o",
                        repo="r",
                        json_file="app/demo.json",
                    )
                ]
            )
        )
        logger = FeatherLogger.setup("ERROR")
        client = MagicMock()
        client.extract_release_info.side_effect = RuntimeError("boom")

        updater = RepositoryUpdater(config, logger, github_client=client)
        result = updater.update_all()

        self.assertFalse(result.success)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.updated_count, 0)


class DateFormatTests(unittest.TestCase):
    def test_iso_and_short(self):
        dt = datetime(2026, 3, 14, 7, 53, 35, tzinfo=timezone.utc)
        self.assertTrue(ReleaseInfoExtractor.format_iso_date(dt).startswith("2026-03-14"))
        self.assertEqual(ReleaseInfoExtractor.format_date_short(dt), "2026-03-14")


if __name__ == "__main__":
    unittest.main()
