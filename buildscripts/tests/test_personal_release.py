from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from personal_release import check_build_number, digest, draft


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
