import XCTest
@testable import NetNewsWire

final class SoftwareUpdateSettingsTests: XCTestCase {

	func testUpdatesRequireExplicitEnablementAndForkFeed() {
		var info: [String: Any] = [
			"SUFeedURL": "https://rhymeswithjazz.github.io/NetNewsWire/appcast.xml",
			"SUPublicEDKey": Data(repeating: 1, count: 32).base64EncodedString()
		]
		XCTAssertFalse(SoftwareUpdateSettings(info: info).isEnabled)
		info["ForkSoftwareUpdatesEnabled"] = "YES"
		XCTAssertTrue(SoftwareUpdateSettings(info: info).isEnabled)
		info["SUFeedURL"] = "https://ranchero.com/downloads/netnewswire-release.xml"
		XCTAssertFalse(SoftwareUpdateSettings(info: info).isEnabled)
	}

	func testMissingSigningKeyDisablesUpdates() {
		let info: [String: Any] = [
			"ForkSoftwareUpdatesEnabled": "YES",
			"SUFeedURL": "https://rhymeswithjazz.github.io/NetNewsWire/appcast.xml"
		]
		XCTAssertFalse(SoftwareUpdateSettings(info: info).isEnabled)
	}

	func testMigrationRemovesUpstreamURLAndPreservesChannelChoice() throws {
		let suite = "SoftwareUpdateSettingsTests.\(UUID().uuidString)"
		let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
		defer { defaults.removePersistentDomain(forName: suite) }
		defaults.set("https://ranchero.com/downloads/netnewswire-beta.xml", forKey: "SUFeedURL")
		let settings = SoftwareUpdateSettings(info: [:])
		settings.migratePreferences(defaults)
		XCTAssertNil(defaults.string(forKey: "SUFeedURL"))
		XCTAssertTrue(defaults.bool(forKey: SoftwareUpdateSettings.testBuildsKey))
		defaults.set(false, forKey: SoftwareUpdateSettings.testBuildsKey)
		defaults.set("https://example.com/old-feed.xml", forKey: "SUFeedURL")
		settings.migratePreferences(defaults)
		XCTAssertNil(defaults.string(forKey: "SUFeedURL"))
		XCTAssertFalse(defaults.bool(forKey: SoftwareUpdateSettings.testBuildsKey))
	}
}
