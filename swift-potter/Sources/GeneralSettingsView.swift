import SwiftUI

@available(macOS 14.0, *)
struct GeneralSettingsView: View {
    @StateObject private var loginItemsManager = LoginItemsManager.shared
    @State private var debugLogClipboard = UserDefaults.standard.bool(forKey: UserDefaultsKeys.debugLogClipboard)

    var body: some View {
        ScrollView(.vertical, showsIndicators: true) {
            VStack(alignment: .leading, spacing: 20) {
                Text("General")
                    .font(.title)
                    .fontWeight(.semibold)
                    .padding(.top, 20)

                LLMProviderView()
                    .padding(.bottom, 10)

                GroupBox("Global Hotkey") {
                    HotkeyView()
                        .padding(.vertical, 8)
                }
                .padding(.bottom, 10)

                GroupBox("Startup") {
                    startAtLoginView
                        .padding(.vertical, 8)
                }
                .padding(.bottom, 10)

                GroupBox("Debug") {
                    debugSection
                        .padding(.vertical, 8)
                }
                .padding(.bottom, 10)

                Color.clear
                    .frame(height: 50)
            }
            .padding(.horizontal, 20)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var debugSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Toggle("Log clipboard data", isOn: $debugLogClipboard)
                    .onChange(of: debugLogClipboard) { newValue in
                        UserDefaults.standard.set(newValue, forKey: UserDefaultsKeys.debugLogClipboard)
                    }
                Spacer()
            }

            Text("When enabled, full clipboard text is logged instead of being redacted. Useful for debugging text processing issues. View logs in the Logs tab.")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.leading, 20)

            if debugLogClipboard {
                HStack(spacing: 4) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                        .font(.caption)
                    Text("Clipboard contents will be visible in logs. Disable after debugging.")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
                .padding(.leading, 20)
            }
        }
    }

    private var startAtLoginView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Toggle("Start Potter at login", isOn: Binding(
                    get: { loginItemsManager.isEnabled },
                    set: { newValue in
                        if newValue {
                            loginItemsManager.enable()
                        } else {
                            loginItemsManager.disable()
                        }
                    }
                ))
                Spacer()
            }

            Text("Potter will automatically start when you log in to your Mac.")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.leading, 20)
        }
        .onAppear {
            loginItemsManager.checkCurrentStatus()
        }
    }
}
