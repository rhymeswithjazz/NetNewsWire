# Follow-up work

## Add a Sparkle update feed for this fork

Software updates are disabled through `AppDefaults.softwareUpdatesEnabled` until this fork has its own release feed.

- Choose hosting for the appcast and release ZIPs. Start with GitHub Pages and GitHub Releases if public downloads are acceptable.
- Replace both Ranchero feed URLs and migrate saved feed preferences so no update path points upstream.
- Generate a Sparkle signing key, embed the public key, and keep the private key outside the repo.
- Automate universal Release archives, Developer ID export, notarization, stapling, ZIP packaging, and signed appcast generation.
- Assign increasing build numbers and publish the download before updating the appcast.
- Verify an update between two fork builds on another Mac, including signature validation and preservation of user data.
- Re-enable Sparkle and the update controls only after the fork feed works.
