import XCTest
@testable import NetNewsWire

final class KeyboardShortcutProfileTests: XCTestCase {
	func testStandardProfileIsUnchanged() {
		let standard = [["key": "k", "action": "markAllAsRead:"], ["key": "l", "action": "advance:"]]
		XCTAssertEqual(KeyboardShortcutProfile.entries(standard, style: .standard, context: .global).count, standard.count)
	}

	func testVimGlobalRemovesOnlyUnmodifiedConflicts() {
		let standard: [[String: Any]] = [
			["key": "k", "action": "markAllAsRead:"],
			["key": "l", "action": "advance:"],
			["key": "k", "action": "markAllAsRead:", "commandModifier": true],
			["key": "n", "action": "nextUnread:"]
		]
		let entries = KeyboardShortcutProfile.entries(standard, style: .vim, context: .global)
		XCTAssertEqual(entries.count, 2)
		XCTAssertTrue(entries.contains { $0["commandModifier"] as? Bool == true })
	}

	func testVimPaneMappingsAreUnique() {
		for context in [KeyboardShortcutContext.sidebar, .timeline, .detail] {
			let entries = KeyboardShortcutProfile.entries([], style: .vim, context: context)
			let keys = entries.compactMap { $0["key"] as? String }
			XCTAssertEqual(keys.count, Set(keys).count)
		}
	}

	func testVimNavigationActions() {
		let timeline = KeyboardShortcutProfile.entries([], style: .vim, context: .timeline)
		XCTAssertEqual(action(for: "j", in: timeline), "selectNextDown:")
		XCTAssertEqual(action(for: "k", in: timeline), "selectNextUp:")
		XCTAssertEqual(action(for: "h", in: timeline), "navigateToSidebar:")
		XCTAssertEqual(action(for: "l", in: timeline), "navigateToDetail:")
	}

	private func action(for key: String, in entries: [[String: Any]]) -> String? {
		entries.first { $0["key"] as? String == key }?["action"] as? String
	}
}
