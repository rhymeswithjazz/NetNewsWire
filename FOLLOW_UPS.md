# Follow-up work

## Add a Sparkle update feed for this fork

The implementation and release commands are documented in [Personal releases](Technotes/PersonalReleases.md). Development builds keep updates disabled; packaged personal releases enable the fork feed.

- [x] Replace Ranchero feeds and migrate saved preferences.
- [x] Generate a Sparkle key and embed the public key.
- [x] Add local packaging and draft release commands.
- [x] Add a GitHub Pages workflow that publishes the feed after release assets are available.
- [x] Install a Developer ID Application certificate and store notarization credentials.
- [x] Validate Developer ID export, Apple notarization, Gatekeeper acceptance, and the signed ZIP/appcast locally.
- [x] Enable GitHub Pages for Actions, allowing main and personal release tags.
- [ ] Merge the workflow and publish the initial feed.
- [ ] Package and manually install the first personal release.
- [ ] Verify an update between two fork builds on another Mac, including signature validation and preservation of user data.
