#!/usr/bin/env python3
"""Build a notarized personal release, then upload it as a separate draft step."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import time

from personal_appcast import REPOSITORY, published_releases, read_item


ROOT = Path(__file__).resolve().parents[1]
DERIVED_DATA = ROOT / "build/personal/DerivedData"
KEY_ACCOUNT = "com.rhymeswithjazz.NetNewsWire"
TEAM_ID = "T4VMW3KDVX"
BUNDLE_ID = "com.rhymeswithjazz.NetNewsWire-Evergreen"


def run(*command, capture=False, log=None):
    if log:
        with log.open("a") as stream:
            subprocess.run(command, cwd=ROOT, check=True, stdout=stream, stderr=subprocess.STDOUT)
        return ""
    return subprocess.check_output(command, cwd=ROOT, text=True).strip() if capture else subprocess.run(command, cwd=ROOT, check=True)


def sparkle_bin(args):
    return Path(args.sparkle_bin).expanduser().resolve() if args.sparkle_bin else DERIVED_DATA / "SourcePackages/artifacts/sparkle/Sparkle/bin"


def public_key():
    with (ROOT / "Mac/Resources/Info.plist").open("rb") as stream:
        return plistlib.load(stream)["SUPublicEDKey"]


def preflight(args):
    problems = []
    for tool in ("xcodebuild", "xcrun", "gh", "ditto", "codesign", "lipo"):
        if not shutil.which(tool):
            problems.append(f"Install {tool}")
    if problems:
        raise ValueError("\n".join(problems))
    tools = sparkle_bin(args)
    if not all((tools / name).is_file() for name in ("generate_keys", "generate_appcast", "sign_update")):
        problems.append("Run the setup command to resolve Sparkle tools, or pass --sparkle-bin")
    else:
        try:
            key = run(str(tools / "generate_keys"), "--account", KEY_ACCOUNT, "-p", capture=True)
            if key != public_key():
                problems.append("The Sparkle key in Keychain must match Info.plist; see Technotes/PersonalReleases.md for recovery")
        except subprocess.CalledProcessError:
            problems.append("Import the fork's Sparkle signing key into Keychain")
    if args.notary_profile:
        try:
            run("xcrun", "notarytool", "history", "--keychain-profile", args.notary_profile, "--output-format", "json", capture=True)
        except subprocess.CalledProcessError:
            problems.append(f"Store working notarization credentials using: xcrun notarytool store-credentials {args.notary_profile}")
    if problems:
        raise ValueError("\n".join(problems))
    print("Sparkle key matches the app. Xcode will select the Developer ID certificate during export.")
    if not args.notary_profile:
        print("Notarization will use the account signed in to Xcode.")


def verify_developer_id(app):
    result = subprocess.run(("codesign", "-dv", "--verbose=4", str(app)), cwd=ROOT,
                            check=True, text=True, capture_output=True)
    details = result.stdout + result.stderr
    if (f"TeamIdentifier={TEAM_ID}" not in details or
            not re.search(r"^Authority=Developer ID Application: .+ \(" + TEAM_ID + r"\)$", details, re.MULTILINE)):
        raise ValueError(f"Exported app is not signed with a Developer ID Application certificate for team {TEAM_ID}")


def check_build_number(build):
    previous = [7210]
    for release in published_releases(include_manual=True):
        suffix = release["tag_name"].split("-", 1)[1]
        if not suffix.isascii() or not suffix.isdecimal():
            raise ValueError(f"Unexpected release tag: {release['tag_name']}")
        previous.append(int(suffix))
    if build <= max(previous):
        raise ValueError(f"Build number must exceed {max(previous)}")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_version(version, beta):
    if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:b[0-9]+)?", version):
        raise ValueError("Use an upstream version such as 7.1.4 or 7.2b3")
    if "b" in version and not beta:
        raise ValueError("A beta version requires --beta")


def export_notarized_archive(archive, output):
    options = output / "ExportOptionsUpload.plist"
    with options.open("wb") as stream:
        plistlib.dump({"method": "developer-id", "teamID": TEAM_ID,
                      "signingStyle": "automatic", "destination": "upload"}, stream)
    print("Signing and submitting to Apple using the Xcode account…", flush=True)
    run("xcodebuild", "-exportArchive", "-archivePath", str(archive),
        "-exportOptionsPlist", str(options), "-allowProvisioningUpdates", log=output / "notarization.log")
    deadline = time.monotonic() + 1200
    while True:
        result = subprocess.run(("xcodebuild", "-exportNotarizedApp", "-archivePath", str(archive),
                                 "-exportPath", str(output / "export")), cwd=ROOT,
                                text=True, capture_output=True)
        details = result.stdout + result.stderr
        with (output / "notarization.log").open("a") as stream:
            stream.write(details)
        if result.returncode == 0:
            return
        if "is processing and not ready for distribution" not in details:
            raise ValueError(f"Notarized export failed: {details.strip()}")
        if time.monotonic() >= deadline:
            raise ValueError(f"Apple is still processing the archive; export it later with xcodebuild -exportNotarizedApp -archivePath {archive} -exportPath {output / 'export'}")
        print("Apple is still processing notarization; checking again in 30 seconds…", flush=True)
        time.sleep(30)


def package(args):
    validate_version(args.version, args.beta)
    if not args.notes.is_file():
        raise ValueError("--notes must name a release notes file")
    if run("git", "status", "--porcelain", capture=True):
        raise ValueError("Commit the working tree before packaging a release")
    preflight(args)
    check_build_number(args.build)
    commit = run("git", "rev-parse", "HEAD", capture=True)
    output = ROOT / f"build/personal/releases/{args.build}"
    output.mkdir(parents=True, exist_ok=False)
    print(f"Building release {args.build}. Build output: {output / 'build.log'}", flush=True)
    archive = output / "NetNewsWire.xcarchive"
    run("xcodebuild", "-project", "NetNewsWire.xcodeproj", "-scheme", "NetNewsWire",
        "-configuration", "Release", "-destination", "generic/platform=macOS",
        "-derivedDataPath", str(DERIVED_DATA), "-archivePath", str(archive),
        "-disableAutomaticPackageResolution", "-allowProvisioningUpdates",
        "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO", f"DEVELOPMENT_TEAM={TEAM_ID}",
        "ORGANIZATION_IDENTIFIER=com.rhymeswithjazz", "DEVELOPER_ENTITLEMENTS=-dev",
        f"CURRENT_PROJECT_VERSION={args.build}", f"MARKETING_VERSION={args.version}",
        "FORK_SOFTWARE_UPDATES_ENABLED=YES", "archive", log=output / "build.log")
    run("bash", "buildscripts/fail_on_warnings.sh", str(output / "build.log"))
    exported = output / "export"
    if args.notary_profile:
        export_options = output / "ExportOptions.plist"
        with export_options.open("wb") as stream:
            plistlib.dump({"method": "developer-id", "teamID": TEAM_ID,
                          "signingStyle": "automatic", "signingCertificate": "Developer ID Application"}, stream)
        run("xcodebuild", "-exportArchive", "-archivePath", str(archive),
            "-exportPath", str(exported), "-exportOptionsPlist", str(export_options),
            "-allowProvisioningUpdates", log=output / "build.log")
    else:
        export_notarized_archive(archive, output)
    app = exported / "NetNewsWire.app"
    with (app / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    expected = {"CFBundleIdentifier": BUNDLE_ID, "CFBundleVersion": str(args.build),
                "CFBundleShortVersionString": args.version,
                "SUPublicEDKey": public_key(), "ForkSoftwareUpdatesEnabled": "YES",
                "SUFeedURL": "https://rhymeswithjazz.github.io/NetNewsWire/appcast.xml"}
    if any(info.get(key) != value for key, value in expected.items()):
        raise ValueError("Exported app does not match the personal release settings")
    architectures = run("lipo", "-archs", str(app / "Contents/MacOS/NetNewsWire"), capture=True).split()
    if set(architectures) != {"arm64", "x86_64"}:
        raise ValueError("Exported app must support Apple Silicon and Intel")
    run("codesign", "--verify", "--deep", "--strict", str(app))
    verify_developer_id(app)
    if args.notary_profile:
        submission = output / "notarization.zip"
        run("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app), str(submission))
        result = json.loads(run("xcrun", "notarytool", "submit", str(submission),
                               "--keychain-profile", args.notary_profile, "--wait", "--output-format", "json", capture=True))
        (output / "notarization.json").write_text(json.dumps(result, indent=2) + "\n")
        if result.get("status") != "Accepted":
            raise ValueError(f"Notarization failed; inspect submission {result.get('id')} with notarytool log")
        run("xcrun", "stapler", "staple", str(app))
    run("xcrun", "stapler", "validate", str(app))
    run("codesign", "--verify", "--deep", "--strict", str(app))
    run("spctl", "--assess", "--type", "execute", "--verbose", str(app))
    payload = output / "payload"
    payload.mkdir()
    zip_path = payload / f"NetNewsWire-{args.build}.zip"
    run("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app), str(zip_path))
    shutil.copyfile(args.notes, zip_path.with_suffix(".md"))
    shutil.copyfile(args.notes, output / "notes.md")
    tag = f"personal-{args.build}"
    tools = sparkle_bin(args)
    command = [str(tools / "generate_appcast"), "--account", KEY_ACCOUNT,
               "--download-url-prefix", f"https://github.com/{REPOSITORY}/releases/download/{tag}/",
               "--link", f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
               "--maximum-deltas", "0", "--embed-release-notes", "-o", str(output / "appcast.xml")]
    if args.beta:
        command.extend(["--channel", "beta"])
    run(*command, str(payload))
    release = {"tag_name": tag, "prerelease": args.beta,
               "assets": [{"name": zip_path.name, "size": zip_path.stat().st_size}]}
    _, item = read_item((output / "appcast.xml").read_bytes(), release)
    signature = item.find("enclosure").get("{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature")
    run(str(tools / "sign_update"), "--account", KEY_ACCOUNT, "--verify", str(zip_path), signature)
    manifest = {"version": args.version, "build": args.build, "beta": args.beta, "commit": commit,
                "sparkle_public_key": public_key(),
                "sha256": {name: digest(output / name) for name in
                           (f"payload/{zip_path.name}", "appcast.xml", "notes.md")}}
    (output / "release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Ready for review: {output}\nCreate a draft with: python3 buildscripts/personal_release.py draft {output}")


def draft(args):
    output = args.directory.resolve()
    manifest = json.loads((output / "release.json").read_text())
    for name, expected in manifest["sha256"].items():
        if digest(output / name) != expected:
            raise ValueError(f"Release artifact changed after packaging: {name}")
    check_build_number(manifest["build"])
    run("gh", "api", f"repos/{REPOSITORY}/commits/{manifest['commit']}", capture=True)
    command = ["gh", "release", "create", f"personal-{manifest['build']}", "--repo", REPOSITORY,
               "--draft", "--target", manifest["commit"],
               "--title", f"NetNewsWire {manifest['version']} personal build {manifest['build']}",
               "--notes-file", str(output / "notes.md")]
    if manifest["beta"]:
        command.append("--prerelease")
    run(*command, str(output / "appcast.xml"), str(output / f"payload/NetNewsWire-{manifest['build']}.zip"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="Resolve the pinned Sparkle tools with Xcode")
    for name in ("preflight", "package"):
        child = commands.add_parser(name)
        child.add_argument("--sparkle-bin", default=os.environ.get("SPARKLE_BIN"))
        child.add_argument("--notary-profile", help="Use this notarytool Keychain profile instead of the Xcode account")
        if name == "package":
            child.add_argument("--version", required=True)
            child.add_argument("--build", required=True, type=int)
            child.add_argument("--beta", action="store_true")
            child.add_argument("--notes", required=True, type=Path)
    child = commands.add_parser("draft")
    child.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "setup":
        run("xcodebuild", "-resolvePackageDependencies", "-project", "NetNewsWire.xcodeproj",
            "-scheme", "NetNewsWire", "-derivedDataPath", str(DERIVED_DATA), "-onlyUsePackageVersionsFromResolvedFile")
    else:
        {"preflight": preflight, "package": package, "draft": draft}[args.command](args)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError, OSError) as error:
        sys.exit(str(error))
