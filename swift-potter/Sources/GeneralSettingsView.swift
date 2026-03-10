import SwiftUI

@available(macOS 14.0, *)
struct GeneralSettingsView: View {
    @StateObject private var loginItemsManager = LoginItemsManager.shared

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

                Color.clear
                    .frame(height: 50)
            }
            .padding(.horizontal, 20)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
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
