import SwiftUI
import AppKit

class SettingsWindowController: NSWindowController {
    static let shared = SettingsWindowController()
    
    private init() {
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 600, height: 400),
            styleMask: [.titled, .closable, .resizable],
            backing: .buffered,
            defer: false
        )
        
        super.init(window: window)
        
        window.title = "Potter Settings"
        window.center()
        window.isReleasedWhenClosed = false
        
        // Create SwiftUI view
        let settingsView = SettingsView()
        let hostingView = NSHostingView(rootView: settingsView)
        window.contentView = hostingView
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}

struct SettingsView: View {
    @StateObject private var settings = PotterSettings()
    @State private var openaiKey: String = ""
    @State private var selectedProvider = "OpenAI"
    
    private let providers = ["OpenAI", "Anthropic", "Google"]
    
    var body: some View {
        VStack(spacing: 20) {
            // Header
            HStack {
                Image(systemName: "wand.and.stars")
                    .font(.title)
                    .foregroundColor(.blue)
                Text("Potter Settings")
                    .font(.title2)
                    .fontWeight(.semibold)
                Spacer()
            }
            .padding(.horizontal)
            
            Divider()
            
            // Settings Form
            Form {
                Section(header: Text("AI Provider").font(.headline)) {
                    Picker("Provider", selection: $selectedProvider) {
                        ForEach(providers, id: \.self) { provider in
                            Text(provider).tag(provider)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    
                    Group {
                        if selectedProvider == "OpenAI" {
                            apiKeyField(
                                title: "OpenAI API Key",
                                key: $openaiKey,
                                placeholder: "sk-..."
                            )
                        } else if selectedProvider == "Anthropic" {
                            apiKeyField(
                                title: "Anthropic API Key",
                                key: Binding(
                                    get: { settings.anthropicAPIKey ?? "" },
                                    set: { settings.anthropicAPIKey = $0 }
                                ),
                                placeholder: "sk-ant-..."
                            )
                        } else if selectedProvider == "Google" {
                            apiKeyField(
                                title: "Google API Key",
                                key: Binding(
                                    get: { settings.googleAPIKey ?? "" },
                                    set: { settings.googleAPIKey = $0 }
                                ),
                                placeholder: "AI..."
                            )
                        }
                    }
                }
                
                Section(header: Text("Processing Modes").font(.headline)) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Available modes:")
                        ForEach(PromptMode.allCases, id: \.self) { mode in
                            HStack {
                                Image(systemName: "circle.fill")
                                    .foregroundColor(.blue)
                                    .font(.caption)
                                VStack(alignment: .leading) {
                                    Text(mode.displayName)
                                        .fontWeight(.medium)
                                    Text(mode.prompt)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                Spacer()
                            }
                        }
                    }
                }
                
                Section(header: Text("Preferences").font(.headline)) {
                    
                    HStack {
                        Text("Global Hotkey: ⌘⇧9")
                        Spacer()
                        Text("(Cannot be changed)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .padding(.horizontal)
            
            Spacer()
            
            // Footer
            HStack {
                Button("Test API Key") {
                    testAPIKey()
                }
                .disabled(getCurrentAPIKey().isEmpty)
                
                Spacer()
                
                Button("Save & Close") {
                    saveSettings()
                    SettingsWindowController.shared.close()
                }
                .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal)
            .padding(.bottom)
        }
        .frame(minWidth: 600, minHeight: 400)
        .onAppear {
            loadSettings()
        }
    }
    
    @ViewBuilder
    private func apiKeyField(title: String, key: Binding<String>, placeholder: String) -> some View {
        VStack(alignment: .leading) {
            Text(title)
                .fontWeight(.medium)
            SecureField(placeholder, text: key)
                .textFieldStyle(RoundedBorderTextFieldStyle())
        }
    }
    
    private func getCurrentAPIKey() -> String {
        switch selectedProvider {
        case "OpenAI":
            return openaiKey
        case "Anthropic":
            return settings.anthropicAPIKey ?? ""
        case "Google":
            return settings.googleAPIKey ?? ""
        default:
            return ""
        }
    }
    
    private func loadSettings() {
        openaiKey = settings.openaiAPIKey ?? ""
        selectedProvider = settings.currentProvider.capitalized
    }
    
    private func saveSettings() {
        switch selectedProvider {
        case "OpenAI":
            settings.openaiAPIKey = openaiKey.isEmpty ? nil : openaiKey
        case "Anthropic":
            // Already bound
            break
        case "Google":
            // Already bound
            break
        default:
            break
        }
        
        settings.currentProvider = selectedProvider.lowercased()
        settings.save()
        
        // Show confirmation
        let alert = NSAlert()
        alert.messageText = "Settings Saved"
        alert.informativeText = "Your settings have been saved successfully."
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
    
    private func testAPIKey() {
        let key = getCurrentAPIKey()
        guard !key.isEmpty else { return }
        
        Task {
            do {
                let client = OpenAIClient(apiKey: key)
                let _ = try await client.processText("Hello", prompt: "Say hi back", model: "gpt-4o-mini")
                
                DispatchQueue.main.async {
                    let alert = NSAlert()
                    alert.messageText = "API Key Valid"
                    alert.informativeText = "Your API key is working correctly!"
                    alert.addButton(withTitle: "OK")
                    alert.runModal()
                }
            } catch {
                DispatchQueue.main.async {
                    let alert = NSAlert()
                    alert.messageText = "API Key Test Failed"
                    alert.informativeText = error.localizedDescription
                    alert.addButton(withTitle: "OK")
                    alert.runModal()
                }
            }
        }
    }
}