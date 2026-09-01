//
//  KeyboardShortcutStyle.swift
//  NetNewsWire
//

import Foundation

extension Notification.Name {
	static let keyboardShortcutStyleDidChange = Notification.Name("KeyboardShortcutStyleDidChangeNotification")
}

enum KeyboardShortcutStyle: Int, CaseIterable, Sendable {
	case standard = 0
	case vim = 1

	var localizedName: String {
		switch self {
		case .standard:
			return NSLocalizedString("Standard", comment: "Keyboard shortcut style")
		case .vim:
			return NSLocalizedString("Vim Style", comment: "Keyboard shortcut style")
		}
	}
}

enum KeyboardShortcutContext: Sendable {
	case global
	case sidebar
	case timeline
	case detail
}

enum KeyboardShortcutProfile {
	static func entries(_ standardEntries: [[String: Any]], style: KeyboardShortcutStyle, context: KeyboardShortcutContext) -> [[String: Any]] {
		guard style == .vim else {
			return standardEntries
		}

		var entries = standardEntries.filter { entry in
			guard context == .global,
				  entry["commandModifier"] as? Bool != true,
				  entry["optionModifier"] as? Bool != true,
				  entry["controlModifier"] as? Bool != true else {
				return true
			}
			return entry["key"] as? String != "k" && entry["key"] as? String != "l"
		}

		entries.append(contentsOf: vimEntries(for: context))
		return entries
	}

	private static func vimEntries(for context: KeyboardShortcutContext) -> [[String: Any]] {
		switch context {
		case .global:
			return []
		case .sidebar:
			return [
				["key": "j", "action": "selectNextDown:", "title": "Select Next Down"],
				["key": "k", "action": "selectNextUp:", "title": "Select Next Up"],
				["key": "h", "action": "collapseSelectedRows:", "title": "Collapse Selected Row"],
				["key": "l", "action": "expandSelectedRowsOrNavigateToTimeline:", "title": "Expand or Navigate to Timeline"]
			]
		case .timeline:
			return [
				["key": "j", "action": "selectNextDown:", "title": "Select Next Down"],
				["key": "k", "action": "selectNextUp:", "title": "Select Next Up"],
				["key": "h", "action": "navigateToSidebar:", "title": "Navigate to Feeds"],
				["key": "l", "action": "navigateToDetail:", "title": "Navigate to Detail"]
			]
		case .detail:
			return [
				["key": "j", "action": "scrollPageDown:", "title": "Scroll Down"],
				["key": "k", "action": "scrollPageUp:", "title": "Scroll Up"],
				["key": "h", "action": "navigateToTimeline:", "title": "Navigate to Timeline"]
			]
		}
	}
}
