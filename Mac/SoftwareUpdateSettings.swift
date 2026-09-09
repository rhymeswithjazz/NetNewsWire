import Foundation

struct SoftwareUpdateSettings {

	static let shared = SoftwareUpdateSettings(info: Bundle.main.infoDictionary ?? [:])
	static let testBuildsKey = "ForkIncludeTestBuilds"

	let feedURL: String
	let isEnabled: Bool

	init(info: [String: Any]) {
		feedURL = info["SUFeedURL"] as? String ?? ""
		let publicKey = info["SUPublicEDKey"] as? String ?? ""
		isEnabled = info["ForkSoftwareUpdatesEnabled"] as? String == "YES"
			&& feedURL == "https://rhymeswithjazz.github.io/NetNewsWire/appcast.xml"
			&& Data(base64Encoded: publicKey)?.count == 32
	}

	func migratePreferences(_ defaults: UserDefaults) {
		if defaults.object(forKey: Self.testBuildsKey) == nil {
			let legacyFeed = defaults.string(forKey: "SUFeedURL")
			defaults.set(legacyFeed == "https://ranchero.com/downloads/netnewswire-beta.xml", forKey: Self.testBuildsKey)
		}
		defaults.removeObject(forKey: "SUFeedURL")
	}
}
