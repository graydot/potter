import SwiftUI
import AppKit

// MARK: - LLM Provider Configuration View
struct LLMProviderView: View {
    @StateObject private var viewModel = LLMProviderViewModel()

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("AI Provider Configuration")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.primary)

            Text("Click a provider card to make it active. Expand to configure API key and model tiers.")
                .font(.caption)
                .foregroundColor(.secondary)

            VStack(spacing: 12) {
                ForEach(LLMProvider.allCases, id: \.self) { provider in
                    ProviderCard(provider: provider, viewModel: viewModel)
                }
            }
        }
        .onChange(of: viewModel.selectedProvider) { newProvider in
            viewModel.onProviderChanged(to: newProvider)
        }
    }
}

// MARK: - Custom Secure Text Field with Paste Support
class PasteableSecureTextField: NSSecureTextField {
    weak var coordinator: CustomAPIKeyField.Coordinator?
    
    override func keyDown(with event: NSEvent) {
        // Handle Cmd+V specifically
        if event.modifierFlags.contains(.command) && event.characters == "v" {
            pasteText()
            return
        }
        super.keyDown(with: event)
    }
    
    @objc func pasteText() {
        if let clipboard = NSPasteboard.general.string(forType: .string) {
            self.stringValue = clipboard
            // Notify coordinator of the change
            coordinator?.textDidChange(with: clipboard)
        }
    }
    
    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        // Handle Cmd+V
        if event.modifierFlags.contains(.command) && event.characters == "v" {
            pasteText()
            return true
        }
        return super.performKeyEquivalent(with: event)
    }
}

// MARK: - Custom API Key Field with Paste Support
struct CustomAPIKeyField: NSViewRepresentable {
    let placeholder: String
    @Binding var text: String
    let borderColor: Color
    
    func makeNSView(context: Context) -> PasteableSecureTextField {
        let textField = PasteableSecureTextField()
        textField.placeholderString = placeholder
        textField.delegate = context.coordinator
        textField.target = context.coordinator
        textField.action = #selector(Coordinator.objcTextDidChange)
        textField.coordinator = context.coordinator
        
        // Style the text field
        textField.isBezeled = true
        textField.bezelStyle = .roundedBezel
        textField.font = NSFont.systemFont(ofSize: 13)
        
        return textField
    }
    
    func updateNSView(_ nsView: PasteableSecureTextField, context: Context) {
        nsView.stringValue = text
        nsView.placeholderString = placeholder
        
        // Update border color
        if let cell = nsView.cell as? NSTextFieldCell {
            switch borderColor {
            case .red:
                cell.backgroundColor = NSColor.red.withAlphaComponent(0.1)
                nsView.layer?.borderColor = NSColor.red.cgColor
                nsView.layer?.borderWidth = 1
            case .green:
                cell.backgroundColor = NSColor.green.withAlphaComponent(0.1)
                nsView.layer?.borderColor = NSColor.green.cgColor
                nsView.layer?.borderWidth = 1
            case .blue:
                cell.backgroundColor = NSColor.blue.withAlphaComponent(0.1)
                nsView.layer?.borderColor = NSColor.blue.cgColor
                nsView.layer?.borderWidth = 1
            default:
                cell.backgroundColor = NSColor.controlBackgroundColor
                nsView.layer?.borderColor = NSColor.clear.cgColor
                nsView.layer?.borderWidth = 0
            }
        }
        
        nsView.wantsLayer = true
        nsView.layer?.cornerRadius = 6
    }
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, NSTextFieldDelegate {
        let parent: CustomAPIKeyField
        
        init(_ parent: CustomAPIKeyField) {
            self.parent = parent
        }
        
        @objc func objcTextDidChange() {
            guard let textField = NSApp.keyWindow?.firstResponder as? NSSecureTextField else { return }
            DispatchQueue.main.async {
                self.parent.text = textField.stringValue
            }
        }
        
        func textDidChange(with newText: String) {
            DispatchQueue.main.async {
                self.parent.text = newText
            }
        }
        
        func controlTextDidChange(_ obj: Notification) {
            guard let textField = obj.object as? NSSecureTextField else { return }
            DispatchQueue.main.async {
                self.parent.text = textField.stringValue
            }
        }
        
        func controlTextDidEndEditing(_ obj: Notification) {
            guard let textField = obj.object as? NSSecureTextField else { return }
            DispatchQueue.main.async {
                self.parent.text = textField.stringValue
            }
        }
        
        // Enable all text editing operations including paste
        func control(_ control: NSControl, textView: NSTextView, doCommandBy commandSelector: Selector) -> Bool {
            // Allow all commands (including paste)
            return false
        }
    }
}

// MARK: - Provider Card

/// A selectable card for a single provider.
/// - Clicking the header selects this provider as active.
/// - The active provider has an accent border and is auto-expanded.
/// - Inside: API key entry + Fast / Standard / Thinking model pickers.
struct ProviderCard: View {
    let provider: LLMProvider
    @ObservedObject var viewModel: LLMProviderViewModel

    @State private var isExpanded: Bool

    private var isActive: Bool { viewModel.selectedProvider == provider }

    init(provider: LLMProvider, viewModel: LLMProviderViewModel) {
        self.provider = provider
        self.viewModel = viewModel
        // Active provider starts expanded; others start collapsed.
        _isExpanded = State(initialValue: viewModel.selectedProvider == provider)
    }

    var body: some View {
        VStack(spacing: 0) {
            // Card header — tapping selects this provider
            Button(action: {
                withAnimation(.easeInOut(duration: 0.2)) {
                    viewModel.selectedProvider = provider
                    isExpanded = true
                }
            }) {
                HStack(spacing: 10) {
                    // Active indicator dot
                    Circle()
                        .fill(isActive ? Color.accentColor : Color.clear)
                        .frame(width: 8, height: 8)
                        .overlay(Circle().stroke(isActive ? Color.accentColor : Color(NSColor.separatorColor), lineWidth: 1.5))

                    Text(provider.displayName)
                        .fontWeight(isActive ? .semibold : .regular)
                        .foregroundColor(isActive ? .primary : .secondary)

                    Spacer()

                    if isActive {
                        Text("Active")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.accentColor.opacity(0.15))
                            .foregroundColor(.accentColor)
                            .clipShape(Capsule())
                    }

                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 10)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            if isExpanded {
                Divider()

                let isConfigured = viewModel.isProviderConfigured(provider)

                VStack(spacing: 14) {
                    // API Key row — always shown
                    apiKeySection

                    Divider()

                    // Tier model pickers — always shown, disabled when no API key
                    VStack(alignment: .leading, spacing: 4) {
                        if !isConfigured {
                            Text("Enter your API key above to enable model selection.")
                                .font(.caption)
                                .foregroundColor(.secondary)
                                .padding(.bottom, 4)
                        }
                        tierSection
                    }
                    .disabled(!isConfigured)
                    .opacity(isConfigured ? 1.0 : 0.45)

                    // Refresh row — only when configured
                    if isConfigured {
                        HStack {
                            Spacer()
                            Button(action: {
                                Task {
                                    do {
                                        try await viewModel.refreshModels(for: provider)
                                    } catch {
                                        PotterLogger.shared.error("settings", "Model refresh failed for \(provider.displayName): \(error.localizedDescription)")
                                    }
                                }
                            }) {
                                if viewModel.isRefreshingModels {
                                    ProgressView()
                                        .scaleEffect(0.6)
                                        .frame(width: 14, height: 14)
                                } else {
                                    Label("Refresh models", systemImage: "arrow.clockwise")
                                        .font(.caption)
                                }
                            }
                            .buttonStyle(.plain)
                            .foregroundColor(.secondary)
                            .disabled(viewModel.isRefreshingModels)

                            if let lastFetched = viewModel.lastFetchedText(for: provider) {
                                Text(lastFetched)
                                    .font(.caption2)
                                    .foregroundColor(.secondary.opacity(0.7))
                            }
                        }
                    }
                }
                .padding(12)
            }
        }
        .background(Color(NSColor.controlBackgroundColor))
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(isActive ? Color.accentColor : Color(NSColor.separatorColor),
                        lineWidth: isActive ? 2 : 1)
        )
        // Keep expansion in sync when active provider changes externally
        .onChange(of: viewModel.selectedProvider) { newProvider in
            if newProvider == provider && !isExpanded {
                withAnimation(.easeInOut(duration: 0.2)) { isExpanded = true }
            }
        }
    }

    // MARK: - API Key Section

    private var apiKeySection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Text("API Key")
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
                    .frame(width: 60, alignment: .leading)

                apiKeyField

                validationIndicator

                testSaveButton

                Spacer()
            }

            // Validation error
            if isActive, case .invalid(let msg) = viewModel.currentValidationState {
                Text(msg)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.leading, 68)
            }

            // Storage error
            if isActive && viewModel.showStorageError {
                Text(viewModel.storageErrorMessage)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.leading, 68)
            }

            // Success
            if isActive && viewModel.showingSuccessCheckmark {
                HStack(spacing: 4) {
                    Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
                    Text("Saved").foregroundColor(.green)
                }
                .font(.caption)
                .padding(.leading, 68)
            }

            // Get API key link
            HStack(spacing: 4) {
                Text("Get key:")
                    .font(.caption2)
                    .foregroundColor(.secondary)
                Button(action: { viewModel.openAPIKeyURL() }) {
                    Text(provider.apiKeyURL)
                        .font(.caption2)
                        .foregroundColor(.accentColor)
                        .underline()
                        .lineLimit(1)
                }
                .buttonStyle(.plain)
            }
            .padding(.leading, 68)
        }
    }

    @ViewBuilder
    private var apiKeyField: some View {
        if isActive {
            // Only show editable field for the active (selected) provider
            HStack {
                Group {
                    if viewModel.showAPIKey {
                        TextField(provider.apiKeyPlaceholder, text: $viewModel.apiKeyText)
                    } else {
                        SecureField(provider.apiKeyPlaceholder, text: $viewModel.apiKeyText)
                    }
                }
                .textFieldStyle(.roundedBorder)
                .font(.system(.body, design: .monospaced))
                .overlay(
                    RoundedRectangle(cornerRadius: 6)
                        .stroke(viewModel.textFieldBorderColor, lineWidth: 2)
                )
                .onChange(of: viewModel.apiKeyText) { viewModel.onAPIKeyTextChanged($0) }

                Button(action: { viewModel.toggleAPIKeyVisibility() }) {
                    Image(systemName: viewModel.showAPIKey ? "eye.slash" : "eye")
                        .foregroundColor(.secondary)
                }
                .buttonStyle(.plain)
            }
            .frame(width: 260)
        } else {
            // Non-active providers: show masked placeholder if configured
            let configured = viewModel.isProviderConfigured(provider)
            Text(configured ? "••••••••••••" : "Not configured")
                .font(.system(.body, design: .monospaced))
                .foregroundColor(.secondary)
                .frame(width: 260, alignment: .leading)
        }
    }

    @ViewBuilder
    private var validationIndicator: some View {
        if isActive {
            Group {
                switch viewModel.currentValidationState {
                case .some(.validating):
                    ProgressView().scaleEffect(0.7).frame(width: 20, height: 20)
                default:
                    EmptyView()
                }
            }
            .frame(width: 24, height: 20)
        }
    }

    @ViewBuilder
    private var testSaveButton: some View {
        if isActive {
            HStack(spacing: 6) {
                Button("Test & Save") {
                    Task { await viewModel.testAndSaveAPIKey() }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isTestAndSaveButtonDisabled)

                if viewModel.isValidating {
                    ProgressView().scaleEffect(0.6).frame(width: 14, height: 14)
                }
            }
        }
    }

    // MARK: - Tier Section

    private var tierSection: some View {
        VStack(spacing: 8) {
            ForEach(ModelTier.allCases, id: \.self) { tier in
                tierRow(for: tier)
            }
        }
    }

    @ViewBuilder
    private func tierRow(for tier: ModelTier) -> some View {
        let config = viewModel.tierConfig(for: provider)
        let models = viewModel.availableModels(for: provider).filter { $0.tier == tier }
        let currentModelID = config.modelID(for: tier)
        let firstModel = viewModel.modelsByTier(for: provider).first(where: { $0.tier == tier })?.models.first

        HStack(alignment: .top, spacing: 12) {
            // Tier label + description stacked vertically
            VStack(alignment: .leading, spacing: 2) {
                Text(tier.displayName)
                    .font(.caption)
                    .fontWeight(.semibold)
                Text(tier.description)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            .frame(width: 130, alignment: .leading)

            if models.isEmpty {
                Text("No models available")
                    .font(.caption)
                    .foregroundColor(.secondary)
            } else {
                Picker("", selection: Binding(
                    get: { currentModelID ?? firstModel?.id ?? "" },
                    set: { viewModel.setPreferredModel($0, tier: tier, provider: provider) }
                )) {
                    ForEach(models) { model in
                        Text(model.name).tag(model.id)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                .frame(width: 200)
                .help(models.first(where: { $0.id == currentModelID })?.description ?? firstModel?.description ?? "")
            }

            Spacer()
        }
        .padding(.vertical, 2)
    }
}

// MARK: - Preview
struct LLMProviderView_Previews: PreviewProvider {
    static var previews: some View {
        LLMProviderView()
            .frame(width: 600, height: 400)
            .padding()
    }
}