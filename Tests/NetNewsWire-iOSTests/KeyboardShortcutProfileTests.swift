import XCTest
@testable import NetNewsWire

final class KeyboardShortcutProfileTests: XCTestCase {
	func testVimNavigationMappings() {
		let sidebar = KeyboardShortcutProfile.entries([], style: .vim, context: .sidebar)
		let timeline = KeyboardShortcutProfile.entries([], style: .vim, context: .timeline)
		let detail = KeyboardShortcutProfile.entries([], style: .vim, context: .detail)

		XCTAssertEqual(action(for: "j", in: sidebar), "selectNextDown:")
		XCTAssertEqual(action(for: "l", in: sidebar), "expandSelectedRowsOrNavigateToTimeline:")
		XCTAssertEqual(action(for: "h", in: timeline), "navigateToSidebar:")
		XCTAssertEqual(action(for: "l", in: timeline), "navigateToDetail:")
		XCTAssertEqual(action(for: "j", in: detail), "scrollPageDown:")
		XCTAssertEqual(action(for: "k", in: detail), "scrollPageUp:")
	}

	private func action(for key: String, in entries: [[String: Any]]) -> String? {
		entries.first { $0["key"] as? String == key }?["action"] as? String
	}
}
