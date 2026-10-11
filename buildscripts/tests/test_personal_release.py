from pathlib import Path
import json
import plistlib
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from personal_release import check_build_number, digest, draft, export_notarized_archive, preflight, validate_version


class PersonalReleaseTests(unittest.TestCase):
    def test_build_numbers_advance_across_both_channels(self):
        releases = [{"tag_name": "personal-8001", "prerelease": False},
                    {"tag_name": "personal-8005", "prerelease": True}]
        with patch("personal_release.published_releases", return_value=releases):
            for build in (7210, 8001, 8004, 8005):
                with self.assertRaisesRegex(ValueError, "exceed 8005"):
                    check_build_number(build)
            check_build_number(8006)

    def test_unexpected_personal_tag_stops_packaging(self):
        with patch("personal_release.published_releases", return_value=[{"tag_name": "personal-latest"}]):
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                check_build_number(8001)

    def test_build_number_exceeds_manual_releases(self):
        with patch("personal_release.published_releases", return_value=[{"tag_name": "manual-8005"}]) as releases:
            with self.assertRaisesRegex(ValueError, "exceed 8005"):
                check_build_number(8005)
            check_build_number(8006)
            releases.assert_called_with(include_manual=True)

    def test_beta_version_cannot_be_published_as_stable(self):
        validate_version("7.2b3", True)
        validate_version("7.1.4", False)
        with self.assertRaisesRegex(ValueError, "requires --beta"):
            validate_version("7.2b3", False)
        for version in ("7", "7.2b", "7.2beta3", "7.2.3.4"):
            with self.assertRaises(ValueError):
                validate_version(version, True)

    def test_xcode_preflight_needs_matching_key_but_no_notary_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("generate_keys", "generate_appcast", "sign_update"):
                (Path(directory) / name).touch()
            args = SimpleNamespace(sparkle_bin=directory, notary_profile=None)
            with patch("personal_release.shutil.which", return_value="tool"), \
                 patch("personal_release.public_key", return_value="expected"), \
                 patch("personal_release.run", return_value="expected") as command:
                preflight(args)
                self.assertEqual(command.call_count, 1)
                command.return_value = "wrong-key"
                with self.assertRaisesRegex(ValueError, "must match"):
                    preflight(args)

    def test_notarization_waits_for_processing_then_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            pending = subprocess.CompletedProcess([], 65, "", 'Archive is processing and not ready for distribution.')
            accepted = subprocess.CompletedProcess([], 0, "EXPORT SUCCEEDED", "")
            with patch("personal_release.run"), \
                 patch("personal_release.subprocess.run", side_effect=[pending, accepted]), \
                 patch("personal_release.time.sleep") as sleep:
                export_notarized_archive(output / "App.xcarchive", output)
                sleep.assert_called_once_with(30)
            options = plistlib.loads((output / "ExportOptionsUpload.plist").read_bytes())
            self.assertEqual(options["destination"], "upload")
            self.assertEqual(options["method"], "developer-id")

    def test_notarization_does_not_retry_rejection_or_auth_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for message in ("Archive was rejected", "Authentication failed"):
                result = subprocess.CompletedProcess([], 65, "", message)
                with patch("personal_release.run"), \
                     patch("personal_release.subprocess.run", return_value=result), \
                     patch("personal_release.time.sleep") as sleep:
                    with self.assertRaisesRegex(ValueError, message):
                        export_notarized_archive(output / "App.xcarchive", output)
                    sleep.assert_not_called()

    def test_notarization_processing_has_a_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            pending = subprocess.CompletedProcess([], 65, "", 'Archive is processing and not ready for distribution.')
            with patch("personal_release.run"), \
                 patch("personal_release.subprocess.run", return_value=pending), \
                 patch("personal_release.time.monotonic", side_effect=[0, 1200]), \
                 patch("personal_release.time.sleep") as sleep:
                with self.assertRaisesRegex(ValueError, "export it later"):
                    export_notarized_archive(output / "App.xcarchive", output)
                sleep.assert_not_called()

    def test_changed_artifact_is_not_uploaded(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            asset = output / "appcast.xml"
            asset.write_text("original signed metadata")
            (output / "release.json").write_text(json.dumps({"sha256": {asset.name: digest(asset)}}))
            asset.write_text("changed metadata")
            with patch("personal_release.run") as command:
                with self.assertRaisesRegex(ValueError, "changed after packaging"):
                    draft(SimpleNamespace(directory=output))
                command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
