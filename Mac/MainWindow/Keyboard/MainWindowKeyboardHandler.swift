//
//  MainWindowKeyboardHandler.swift
//  NetNewsWire
//
//  Created by Brent Simmons on 12/19/17.
//  Copyright © 2017 Ranchero Software. All rights reserved.
//

import AppKit
import RSCore

@MainActor final class MainWindowKeyboardHandler: KeyboardDelegate {
	static let shared = MainWindowKeyboardHandler()
	private let shortcutSets = KeyboardShortcutSets(resourceName: "GlobalKeyboardShortcuts", context: .global)
	private var globalShortcuts: Set<KeyboardShortcut> {
		shortcutSets.shortcuts(for: AppDefaults.shared.keyboardShortcutStyle)
	}

	func keydown(_ event: NSEvent, in view: NSView) -> Bool {
		let key = KeyboardKey(with: event)
		guard let matchingShortcut = KeyboardShortcut.findMatchingShortcut(in: globalShortcuts, key: key) else {
			return false
		}

		matchingShortcut.perform(with: view)
		return true
	}
}

struct KeyboardShortcutSets {
	private let standard: Set<KeyboardShortcut>
	private let vim: Set<KeyboardShortcut>

	init(resourceName: String, context: KeyboardShortcutContext) {
		let path = Bundle.main.path(forResource: resourceName, ofType: "plist")!
		let rawEntries = NSArray(contentsOfFile: path)! as! [[String: Any]]
		standard = Set(KeyboardShortcutProfile.entries(rawEntries, style: .standard, context: context).compactMap { KeyboardShortcut(dictionary: $0) })
		vim = Set(KeyboardShortcutProfile.entries(rawEntries, style: .vim, context: context).compactMap { KeyboardShortcut(dictionary: $0) })
	}

	func shortcuts(for style: KeyboardShortcutStyle) -> Set<KeyboardShortcut> {
		style == .vim ? vim : standard
	}
}
