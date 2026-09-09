# Personal Mac releases

The fork uses Sparkle with a feed at <https://rhymeswithjazz.github.io/NetNewsWire/appcast.xml>. ZIPs live in public GitHub Releases on `rhymeswithjazz/NetNewsWire`. One feed carries stable builds and a `beta` channel. Test-build users also receive newer stable builds.

Ordinary builds leave updates disabled. `personal_release.py package` enables them in the exported app. Existing Ranchero feed preferences are removed at startup. The app's delegate fixes the feed URL so a saved preference cannot redirect checks upstream.

## One-time setup

1. Install Python 3.11 or later and GitHub CLI, then run `gh auth login`.
2. In Xcode Settings > Accounts, select your team and open Manage Certificates. Create or import a **Developer ID Application** certificate for team `T4VMW3KDVX`. It must include its private key. An Apple Development certificate is not sufficient for distribution.
3. Store notarization credentials interactively. Use an app-specific password when prompted, never a password in the repo or command history:

   ```sh
   xcrun notarytool store-credentials netnewswire-notary --apple-id YOUR_APPLE_ID --team-id T4VMW3KDVX
   ```

4. Resolve the project's pinned tools:

   ```sh
   python3 buildscripts/personal_release.py setup
   ```

5. The fork's Sparkle key was created in this Mac's login Keychain under account `com.rhymeswithjazz.NetNewsWire`. Only its public key is committed in `Mac/Resources/Info.plist`. Keep a secure backup of the private key. To build releases on a different Mac, import this same key with Sparkle's `generate_keys -f`; do not generate a replacement key. `generate_keys --help` explains key export and import. Store any exported private key outside this repository.
6. Merge the release code into `main`. In the fork's Settings > Pages, set the source to **GitHub Actions**. If the `github-pages` environment limits deployment branches or tags, allow `main` and the `personal-*` tags. Run the **Personal update feed** workflow manually once. With no personal releases, it publishes a valid empty feed.
7. Run the preflight check:

   ```sh
   python3 buildscripts/personal_release.py preflight
   ```

The preflight checks the signing identity, public/private Sparkle key match, and notarization credentials. `--sparkle-bin /path/to/Sparkle/bin` can use tools from an existing Xcode build. `--notary-profile NAME` selects another Keychain profile. macOS may ask you to approve Keychain access for `generate_appcast` or `sign_update` when packaging for the first time.

## Package and publish

Commit the source first. Start personal build numbers at `8001`, then increase them for every stable or beta release. The script rejects numbers at or below any published personal build. Keep the app's bundle identifier and signing team stable.

Write release notes in a file outside the working tree or in an ignored build directory, then run:

```sh
python3 buildscripts/personal_release.py package \
  --version 7.1.4 --build 8001 --notes /tmp/netnewswire-release-notes.md
```

Add `--beta` to publish a test build. Use a three-part marketing version; the separate build number identifies the personal release. Packaging archives both Mac architectures, exports with Developer ID, notarizes, staples the app, verifies Gatekeeper acceptance, and generates a signed ZIP and appcast. It keeps the project's development feature settings, so this does not enable iCloud or other restricted account types.

Files go under `build/personal/releases/8001/`. Build output is in `build.log`. Failed runs keep their files for diagnosis; move that build's output directory aside before retrying the same number.

Review and test `export/NetNewsWire.app`. Push the source commit to the fork, then upload the release as a draft:

```sh
python3 buildscripts/personal_release.py draft build/personal/releases/8001
```

This uploads only the ZIP and its appcast, with your notes and the exact source commit. It does not publish the release. Open the draft in GitHub and publish it when ready. Leave the prerelease setting consistent with the `--beta` choice. The **Personal update feed** workflow validates published release metadata, then deploys the combined feed to Pages. The ZIP is available before the feed advertises it.

Never replace the ZIP or appcast of a published build. Publish a higher build number for fixes. Removing a release and rerunning the workflow removes its feed entry; it does not downgrade Macs that already installed it. Releases without a `personal-` tag are ignored.

## First installation and update test

Install the first notarized personal build manually on each Mac. The currently installed build has updates disabled and cannot bootstrap itself. Once the personal build is installed, subsequent published builds can update through Sparkle.

Before relying on automatic updates:

1. Install build A on a second Mac and add a test feed or other disposable state.
2. Publish a higher build B. Use **Check for Updates** on the second Mac and confirm the displayed version, successful installation, and preserved state.
3. Confirm release-only users do not receive beta builds, while test-build users see both channels.
4. Verify a modified ZIP fails signature validation in a local test feed. Do not upload the modified file to the production feed.

## References

- [Sparkle publishing](https://sparkle-project.org/documentation/publishing/)
- [Apple notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
