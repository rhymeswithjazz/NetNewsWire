//
//  AdvancedPreferencesViewController.swift
//  NetNewsWire
//
//  Created by Brent Simmons on 1/11/19.
//  Copyright © 2019 Ranchero Software. All rights reserved.
//

import AppKit

final class AdvancedPreferencesViewController: NSViewController {

	@IBOutlet var releaseBuildsButton: NSButton!
	@IBOutlet var testBuildsButton: NSButton!

	var didRegisterForNotification = false
	var wantsTestBuilds: Bool {
		get {
			UserDefaults.standard.bool(forKey: SoftwareUpdateSettings.testBuildsKey)
		}
		set {
			UserDefaults.standard.set(newValue, forKey: SoftwareUpdateSettings.testBuildsKey)
		}
	}

	override func viewWillAppear() {
		super.viewWillAppear()
		updateUI()
		if !didRegisterForNotification {
			NotificationCenter.default.addObserver(forName: UserDefaults.didChangeNotification, object: nil, queue: .main) { [weak self] _ in
				Task { @MainActor in
					self?.userDefaultsDidChange()
				}
			}
			didRegisterForNotification = true
		}
	}

	@IBAction func updateTypeButtonClicked(_ sender: Any?) {
		guard SoftwareUpdateSettings.shared.isEnabled, let button = sender as? NSButton else {
			return
		}
		wantsTestBuilds = (button === testBuildsButton)
	}

	func userDefaultsDidChange() {
		updateUI()
	}
}

private extension AdvancedPreferencesViewController {

	func updateUI() {
		releaseBuildsButton.isEnabled = SoftwareUpdateSettings.shared.isEnabled
		testBuildsButton.isEnabled = SoftwareUpdateSettings.shared.isEnabled
		testBuildsButton.state = wantsTestBuilds ? .on : .off
		releaseBuildsButton.state = wantsTestBuilds ? .off : .on
	}
}
