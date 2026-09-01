//
//  DetailKeyboardDelegate.swift
//  NetNewsWire
//
//  Created by Maurice Parker on 3/1/19.
//  Copyright © 2019 Ranchero Software. All rights reserved.
//

import AppKit
import RSCore

@objc final class DetailKeyboardDelegate: NSObject, KeyboardDelegate {

	private let shortcutSets = KeyboardShortcutSets(resourceName: "DetailKeyboardShortcuts", context: .detail)
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
