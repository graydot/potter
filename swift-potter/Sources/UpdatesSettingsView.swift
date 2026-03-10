import SwiftUI

@available(macOS 14.0, *)
struct UpdatesSettingsView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Updates")
                .font(.title)
                .fontWeight(.semibold)

            VStack(alignment: .leading, spacing: 12) {
                Text("Current Version")
                    .font(.headline)

                HStack {
                    Text("Version:")
                        .frame(width: 100, alignment: .leading)
                    Text(AutoUpdateManager.shared.getCurrentVersion())
                        .foregroundColor(.secondary)
                    Spacer()
                }

                HStack {
                    Text("Build:")
                        .frame(width: 100, alignment: .leading)
                    Text(AutoUpdateManager.shared.getBuildNumber())
                        .foregroundColor(.secondary)
                    Spacer()
                }

                if let lastCheck = AutoUpdateManager.shared.getLastUpdateCheckDate() {
                    HStack {
                        Text("Last Check:")
                            .frame(width: 100, alignment: .leading)
                        Text(DateFormatter.localizedString(from: lastCheck, dateStyle: .short, timeStyle: .short))
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)

            VStack(alignment: .leading, spacing: 12) {
                Text("Update Settings")
                    .font(.headline)

                Toggle("Automatically check for updates", isOn: Binding(
                    get: { AutoUpdateManager.shared.getAutoUpdateEnabled() },
                    set: { enabled in
                        AutoUpdateManager.shared.setAutoUpdateEnabled(enabled)
                    }
                ))

                Text("Potter will check for updates daily and notify you when new versions are available.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)

            HStack {
                Button("Check for Updates Now") {
                    AutoUpdateManager.shared.checkForUpdatesManually()
                }
                .buttonStyle(.borderedProminent)

                Spacer()

                Button("Open Releases Page") {
                    if let url = URL(string: "https://github.com/graydot/potter/releases") {
                        NSWorkspace.shared.open(url)
                    }
                }
                .buttonStyle(.bordered)
            }

            Spacer()
        }
    }
}
