import SwiftUI
import Foundation

// MARK: - UIStateStore
//
// Single source of truth for all UI layout and navigation state that must
// survive window resizes (and across app launches).
//
// Design principles:
//   1. Every property that can be lost on a SwiftUI view rebuild lives here.
//   2. Each property is backed by UserDefaults via a private stored value +
//      didSet, so it is automatically persisted without any extra save calls.
//   3. Views access this store via @EnvironmentObject — the root view creates
//      the single instance with @StateObject and injects it.
//   4. Adding new persistent UI state = add one property here + inject the
//      environment object in the relevant view. No other plumbing required.
//
// Keys are namespaced with the "ui_" prefix and are declared in UserDefaultsKeys.swift
// alongside all other app UserDefaults keys.

final class UIStateStore: ObservableObject {

    // MARK: - Singleton
    static let shared = UIStateStore()

    // MARK: - Settings Navigation

    /// Which section is active in the sidebar (0 = General, 1 = Prompts, …).
    @Published var selectedSection: Int {
        didSet { UserDefaults.standard.set(selectedSection, forKey: UserDefaultsKeys.uiSelectedSection) }
    }

    // MARK: - Sidebar / Panel Sizes

    /// Width of the settings sidebar in points.
    @Published var sidebarWidth: Double {
        didSet { UserDefaults.standard.set(sidebarWidth, forKey: UserDefaultsKeys.uiSidebarWidth) }
    }

    // MARK: - Prompts List

    /// UUID string of the currently selected prompt row (nil when nothing selected).
    @Published var selectedPromptIDString: String? {
        didSet { UserDefaults.standard.set(selectedPromptIDString, forKey: UserDefaultsKeys.uiSelectedPromptID) }
    }

    /// UUID string of the prompt row used as the scroll anchor in the list.
    /// Persisting this means the list scrolls back to the same position on resize.
    @Published var scrollAnchorIDString: String? {
        didSet { UserDefaults.standard.set(scrollAnchorIDString, forKey: UserDefaultsKeys.uiScrollAnchorID) }
    }

    // MARK: - Prompt Edit Dialog

    /// Height of the prompt text area in the edit dialog, in points.
    /// A value of 0 means "not yet set by user — use the percentage default".
    @Published var promptTextAreaHeight: Double {
        didSet { UserDefaults.standard.set(promptTextAreaHeight, forKey: UserDefaultsKeys.uiPromptTextAreaHeight) }
    }

    // MARK: - Logs View

    /// Raw string for the selected log filter level (nil = "All").
    @Published var logFilterRaw: String? {
        didSet { UserDefaults.standard.set(logFilterRaw, forKey: UserDefaultsKeys.uiLogFilterRaw) }
    }

    // MARK: - Computed Helpers

    var selectedPromptID: UUID? {
        get { selectedPromptIDString.flatMap { UUID(uuidString: $0) } }
        set { selectedPromptIDString = newValue?.uuidString }
    }

    var scrollAnchorID: UUID? {
        get { scrollAnchorIDString.flatMap { UUID(uuidString: $0) } }
        set { scrollAnchorIDString = newValue?.uuidString }
    }

    // MARK: - Initialisation

    private init() {
        let ud = UserDefaults.standard

        self.selectedSection   = ud.object(forKey: UserDefaultsKeys.uiSelectedSection) != nil
                                    ? ud.integer(forKey: UserDefaultsKeys.uiSelectedSection) : 0
        self.sidebarWidth      = ud.object(forKey: UserDefaultsKeys.uiSidebarWidth) != nil
                                    ? ud.double(forKey: UserDefaultsKeys.uiSidebarWidth)     : 220
        self.selectedPromptIDString = ud.string(forKey: UserDefaultsKeys.uiSelectedPromptID)
        self.scrollAnchorIDString   = ud.string(forKey: UserDefaultsKeys.uiScrollAnchorID)
        self.promptTextAreaHeight   = ud.object(forKey: UserDefaultsKeys.uiPromptTextAreaHeight) != nil
                                    ? ud.double(forKey: UserDefaultsKeys.uiPromptTextAreaHeight) : 0
        self.logFilterRaw           = ud.string(forKey: UserDefaultsKeys.uiLogFilterRaw)
    }

}
