import SwiftUI
import AppKit

@available(macOS 14.0, *)
struct AboutSettingsView: View {
    @StateObject private var promptService = PromptService.shared
    @StateObject private var settings = PotterSettings()

    var body: some View {
        ScrollView(.vertical, showsIndicators: true) {
            VStack(alignment: .leading, spacing: 20) {
                Text("About")
                    .font(.title)
                    .fontWeight(.semibold)

                buildInfoSection
                environmentSection
                privacyWarningSection

                HStack(alignment: .top, spacing: 20) {
                    aboutLinksSection
                    Spacer()
                    dataManagementSection
                        .frame(maxWidth: 200)
                }

                helpSection

                Color.clear
                    .frame(height: 50)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Sections

    private var buildInfoSection: some View {
        GroupBox("Build Information") {
            VStack(alignment: .leading, spacing: 12) {
                let buildInfo = BuildInfo.current()

                VStack(alignment: .leading, spacing: 4) {
                    Text("Build Name")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Text(buildInfo.buildName)
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundColor(.primary)
                }

                Divider()
                    .padding(.vertical, 4)

                infoRow("Version:", "\(buildInfo.version) • \(buildInfo.versionCodename)")
                infoRow("Built:", buildInfo.buildDate)
            }
            .padding()
        }
    }

    private var environmentSection: some View {
        GroupBox("Environment Information") {
            VStack(alignment: .leading, spacing: 10) {
                infoRow("Mode:", "Development")
                infoRow("Swift:", "5.9")
                infoRow("macOS:", ProcessInfo.processInfo.operatingSystemVersionString)
            }
            .padding()
        }
    }

    private var privacyWarningSection: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.orange)
                        .font(.title2)

                    Text("Privacy Warning")
                        .font(.headline)
                        .fontWeight(.semibold)
                }

                Text("This app processes your text using external AI services (Anthropic, Google). Potter and the app author do not store your text or keystrokes, but the AI providers will have access to any text you process. Avoid using this app with sensitive, confidential, or private information.")
                    .foregroundColor(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding()
        }
    }

    private var aboutLinksSection: some View {
        GroupBox("About") {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 4) {
                    Text("Developed by")
                        .foregroundColor(.secondary)

                    Button("graydot") {
                        if let url = URL(string: "https://graydot.ai") {
                            NSWorkspace.shared.open(url)
                        }
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.blue)
                    .underline()

                    Text("with")
                        .foregroundColor(.secondary)

                    Text("♥")
                        .foregroundColor(.red)
                }

                HStack {
                    Text("Product link for Potter:")
                        .foregroundColor(.secondary)

                    Button(action: {
                        if let url = URL(string: "https://graydot.ai/products/potter/") {
                            NSWorkspace.shared.open(url)
                        }
                    }) {
                        HStack(spacing: 4) {
                            if let appIcon = NSImage(named: "AppIcon") {
                                Image(nsImage: appIcon)
                                    .resizable()
                                    .frame(width: 16, height: 16)
                            } else {
                                Image(systemName: "wand.and.stars")
                                    .frame(width: 16, height: 16)
                            }
                            Text("potter")
                        }
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.blue)
                    .underline()
                }

                HStack {
                    Text("Source code:")
                        .foregroundColor(.secondary)

                    Button(action: {
                        if let url = URL(string: "https://github.com/graydot/potter") {
                            NSWorkspace.shared.open(url)
                        }
                    }) {
                        HStack(spacing: 4) {
                            Image(systemName: "chevron.left.forwardslash.chevron.right")
                                .frame(width: 16, height: 16)
                            Text("GitHub")
                        }
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.blue)
                    .underline()
                }
            }
            .padding()
        }
    }

    private var dataManagementSection: some View {
        GroupBox("Data Management") {
            VStack(alignment: .leading, spacing: 12) {
                Text("Remove all Potter data and return to pristine state.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .fixedSize(horizontal: false, vertical: true)

                HStack {
                    Button(action: openPromptsFolder) {
                        HStack(spacing: 4) {
                            Image(systemName: "folder")
                                .frame(width: 14, height: 14)
                            Text("Show prompts folder")
                        }
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.blue)
                    .underline()
                    .font(.caption)

                    Spacer()
                }

                Button("Delete All Data") {
                    showDeleteAllDataDialog()
                }
                .buttonStyle(.bordered)
                .foregroundColor(.red)
            }
            .padding()
        }
    }

    private var helpSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Divider()
                .padding(.bottom, 8)

            HStack {
                Spacer()
                Button("Onboarding/Help") {
                    OnboardingWindowController.shared.showOnboarding()
                }
                .buttonStyle(.bordered)
                .font(.caption)
                Spacer()
            }
        }
        .padding(.top, 20)
    }

    // MARK: - Helpers

    private func infoRow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label)
                .frame(width: 80, alignment: .leading)
            Text(value)
                .foregroundColor(.secondary)
            Spacer()
        }
    }

    private func openPromptsFolder() {
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let potterDir = appSupport.appendingPathComponent("Potter")
        NSWorkspace.shared.open(potterDir)
    }

    private func showDeleteAllDataDialog() {
        let alert = NSAlert()
        alert.messageText = "Delete All Potter Data"
        alert.informativeText = "This will permanently delete all Potter data including prompts, API keys, and settings. This action cannot be undone."
        alert.alertStyle = .critical

        alert.addButton(withTitle: "Cancel")
        let deleteButton = alert.addButton(withTitle: "Wait (5s)")
        deleteButton.isEnabled = false
        deleteButton.contentTintColor = .systemRed

        class CountdownHandler {
            var countdown = 5
            var timer: Timer?
            weak var button: NSButton?

            func start() {
                timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] timer in
                    guard let self = self else {
                        timer.invalidate()
                        return
                    }

                    self.countdown -= 1

                    if self.countdown > 0 {
                        self.button?.title = "Wait (\(self.countdown)s)"
                    } else {
                        self.button?.title = "Delete All"
                        self.button?.isEnabled = true
                        timer.invalidate()
                        self.timer = nil
                    }
                }

                if let timer = timer {
                    RunLoop.main.add(timer, forMode: .common)
                }
            }

            func stop() {
                timer?.invalidate()
                timer = nil
            }
        }

        let handler = CountdownHandler()
        handler.button = deleteButton
        handler.start()

        let response = alert.runModal()
        handler.stop()

        if response == .alertSecondButtonReturn && deleteButton.isEnabled {
            SettingsHelpers.initializeFreshState(promptService: promptService, settings: settings)

            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                let confirmAlert = NSAlert()
                confirmAlert.messageText = "Data Deleted"
                confirmAlert.informativeText = "All Potter data has been deleted. The app has been reset to its initial state."
                confirmAlert.addButton(withTitle: "OK")
                confirmAlert.runModal()
            }
        }
    }
}
