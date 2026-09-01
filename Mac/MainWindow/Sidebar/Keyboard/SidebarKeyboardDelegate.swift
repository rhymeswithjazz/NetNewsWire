//
//  SidebarKeyboardDelegate.swift
//  NetNewsWire
//
//  Created by Brent Simmons on 12/19/17.
//  Copyright © 2017 Ranchero Software. All rights reserved.
//

import AppKit
import RSCore

@objc final class SidebarKeyboardDelegate: NSObject, KeyboardDelegate {

	@IBOutlet var sidebarViewController: SidebarViewController?
	private let shortcutSets = KeyboardShortcutSets(resourceName: "SidebarKeyboardShortcuts", context: .sidebar)
	private var shortcuts: Set<KeyboardShortcut> {
		shortcutSets.shortcuts(for: AppDefaults.shared.keyboardShortcutStyle)
	}

	func keydown(_ event: NSEvent, in view: NSView) -> Bool {

		if MainWindowKeyboardHandler.shared.keydown(event, in: view) {
			return true
		}

		let key = KeyboardKey(with: event)
		guard let matchingShortcut = KeyboardShortcut.findMatchingShortcut(in: shortcuts, key: key) else {
			return false
		}

		matchingShortcut.perform(with: view)
		return true
	}
}
