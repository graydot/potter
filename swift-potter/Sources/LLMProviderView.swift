import SwiftUI
import AppKit

// MARK: - LLM Provider Configuration View
struct LLMProviderView: View {
    @StateObject private var llmManager = LLMManager()
    @State private var apiKeyText: String = ""
    @State private var showingSuccessCheckmark = false
    @State private var showAPIKey = false
    @State private var storageMethod: APIKeyStorageMethod = .userDefaults
    @State private var showStorageError = false
    @State private var storageErrorMessage = ""
    @State private var isMigrating = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            // Section Header
            Text("AI Provider Configuration")
                .font(.title2)
                .fontWeight(.bold)
                .foregroundColor(.primary)
            
            VStack(alignment: .leading, spacing: 16) {
                // Provider Selection
                providerSelectionView
                
                // Model Selection
                modelSelectionView
                
                // API Key Configuration
                apiKeyConfigurationView
            }
            .padding(.leading, 8)
        }
        .onAppear {
            // Load current API key and storage method for display
            apiKeyText = llmManager.getAPIKey(for: llmManager.selectedProvider)
            storageMethod = SecureAPIKeyStorage.shared.getStorageMethod(for: llmManager.selectedProvider)
        }
        .onChange(of: llmManager.selectedProvider) { newProvider in
            // Load API key and storage method for the newly selected provider
            apiKeyText = llmManager.getAPIKey(for: newProvider)
            storageMethod = SecureAPIKeyStorage.shared.getStorageMethod(for: newProvider)
            // Set default model for the new provider
            llmManager.selectedModel = newProvider.models.first
        }
    }
    
    // MARK: - Provider Selection
    private var providerSelectionView: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Provider:")
                    .fontWeight(.medium)
                    .frame(width: 80, alignment: .leading)
                
                Picker("Provider", selection: $llmManager.selectedProvider) {
                    ForEach(LLMProvider.allCases) { provider in
                        HStack {
                            Text(provider.displayName)
                            if llmManager.isProviderConfigured(provider) {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundColor(.green)
                                    .font(.caption)
                            }
                        }
                        .tag(provider)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                .frame(width: 200)
                
                Spacer()
            }
        }
    }
    
    // MARK: - Model Selection
    private var modelSelectionView: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Model:")
                    .fontWeight(.medium)
                    .frame(width: 80, alignment: .leading)
                
                Picker("Model", selection: $llmManager.selectedModel) {
                    ForEach(llmManager.selectedProvider.models) { model in
                        Text(model.name)
                            .tag(model as LLMModel?)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                .frame(width: 200)
                .help(llmManager.selectedModel?.description ?? "Select a model")
                
                Spacer()
            }
            
            // Description text below the picker
            if let selectedModel = llmManager.selectedModel {
                Text(selectedModel.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.leading, 88) // Align with model picker
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
    
    // MARK: - API Key Configuration
    private var apiKeyConfigurationView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("API Key:")
                    .fontWeight(.medium)
                    .frame(width: 80, alignment: .leading)
                
                // API Key Input Field
                HStack {
                    apiKeyTextField
                    
                    // Validation Status
                    validationStatusView
                    
                    // Storage Method Toggle (Lock Icon)
                    storageMethodToggle
                    
                    // Test & Save Button
                    testAndSaveButton
                }
                
                Spacer()
            }
            
            // Validation Error Message
            if case .invalid(let message) = llmManager.validationStates[llmManager.selectedProvider] {
                Text(message)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.leading, 88) // Align with API key field
            }
            
            // Storage Error Message
            if showStorageError {
                Text(storageErrorMessage)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.leading, 88)
            }
            
            // API Key Link - moved up
            HStack {
                Text("Get your API key:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Button(action: {
                    if let url = URL(string: llmManager.selectedProvider.apiKeyURL) {
                        NSWorkspace.shared.open(url)
                    }
                }) {
                    Text(llmManager.selectedProvider.displayName + " API Keys")
                        .font(.caption)
                        .foregroundColor(.blue)
                        .underline()
                }
                .buttonStyle(.plain)
                .help("Open \(llmManager.selectedProvider.displayName) API keys page in browser")
            }
            .padding(.leading, 88) // Align with API key field
            
            // Storage Method Status with Success Message on same line
            HStack(spacing: 6) {
                Text("Storage:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .fixedSize()
                
                if storageMethod == .keychain {
                    Text("Keys encrypted and saved")
                        .font(.caption)
                        .foregroundColor(.green)
                        .fontWeight(.medium)
                        .lineLimit(1)
                    
                    Image(systemName: "lock.fill")
                        .font(.caption)
                        .foregroundColor(.green)
                } else {
                    Text("Keys saved without encryption")
                        .font(.caption)
                        .foregroundColor(.orange)
                        .fontWeight(.medium)
                        .lineLimit(1)
                    
                    Image(systemName: "lock.open.fill")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
                
                // Success Message on the same line, to the right
                if showingSuccessCheckmark {
                    Spacer().frame(width: 20) // Add some space
                    
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                        .font(.caption)
                    
                    Text("API key saved successfully")
                        .font(.caption)
                        .foregroundColor(.green)
                        .transition(.opacity)
                }
                
                Spacer() // Push everything to the left
            }
            .padding(.leading, 88) // Align with API key field
            .frame(maxWidth: .infinity, alignment: .leading)
            .lineLimit(1)
        }
    }
    
    private var apiKeyTextField: some View {
        HStack {
            if showAPIKey {
                TextField(llmManager.selectedProvider.apiKeyPlaceholder, text: $apiKeyText)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(.body, design: .monospaced))
            } else {
                SecureField(llmManager.selectedProvider.apiKeyPlaceholder, text: $apiKeyText)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(.body, design: .monospaced))
            }
            
            Button(action: {
                showAPIKey.toggle()
            }) {
                Image(systemName: showAPIKey ? "eye.slash" : "eye")
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
            .help(showAPIKey ? "Hide API key" : "Show API key")
        }
        .frame(width: 300)
        .onChange(of: apiKeyText) { newValue in
            // Only update the in-memory cache, actual storage happens in Test & Save
            llmManager.apiKeys[llmManager.selectedProvider] = newValue
            llmManager.validationStates[llmManager.selectedProvider] = LLMManager.ValidationState.none
        }
    }
    
    private var textFieldBorderColor: Color {
        switch llmManager.validationStates[llmManager.selectedProvider] {
        case .invalid:
            return .red
        case .valid:
            return .green
        case .validating:
            return .blue
        default:
            return .clear
        }
    }
    
    private var validationStatusView: some View {
        Group {
            switch llmManager.validationStates[llmManager.selectedProvider] {
            case .valid:
                Image(systemName: "checkmark.circle.fill")
                    .foregroundColor(.green)
                    .font(.title3)
                
            case .invalid:
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.red)
                    .font(.title3)
                
            case .validating:
                ProgressView()
                    .scaleEffect(0.7)
                    .frame(width: 20, height: 20)
                
            case .some(.none), .none:
                EmptyView()
            }
        }
        .frame(width: 24, height: 20)
    }
    
    private var testAndSaveButton: some View {
        Button("Test & Save") {
            Task { @MainActor in
                do {
                    // Clear any previous errors
                    showStorageError = false
                    
                    // Update the storage method preference first
                    SecureAPIKeyStorage.shared.setStorageMethod(storageMethod, for: llmManager.selectedProvider)
                    
                    // Then validate and save (this will use the updated storage method)
                    await llmManager.validateAndSaveAPIKey(apiKeyText, for: llmManager.selectedProvider)
                    
                    let success = llmManager.validationStates[llmManager.selectedProvider]?.isValid == true
                    
                    if success {
                        // Show success checkmark briefly if validation succeeded
                        withAnimation(.easeInOut(duration: 0.3)) {
                            showingSuccessCheckmark = true
                        }
                        
                        DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                            withAnimation(.easeInOut(duration: 0.3)) {
                                showingSuccessCheckmark = false
                            }
                        }
                    } else {
                        showStorageError = true
                        let errorMessage = llmManager.validationStates[llmManager.selectedProvider]?.errorMessage ?? "Unknown validation error"
                        storageErrorMessage = "Failed to validate API key: \(errorMessage)"
                        
                        // Hide error after 5 seconds
                        DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                            showStorageError = false
                        }
                    }
            }
        }
        .buttonStyle(.borderedProminent)
        .disabled(apiKeyText.isEmpty || llmManager.isValidating || isMigrating)
    }
    
    private var storageMethodToggle: some View {
        Button(action: {
            toggleStorageMethod()
        }) {
            if isMigrating {
                ProgressView()
                    .scaleEffect(0.7)
                    .frame(width: 24, height: 20)
            } else {
                Image(systemName: storageMethod == .keychain ? "lock.fill" : "lock.open.fill")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(storageMethod == .keychain ? .green : .orange)
                    .frame(width: 24, height: 20)
            }
        }
        .buttonStyle(.plain)
        .disabled(isMigrating)
        .help(isMigrating ? "Migrating API keys..." :
              (storageMethod == .keychain ? 
               "Switch to plain text storage (UserDefaults)" : 
               "Switch to encrypted storage (Keychain)"))
    }
    
    private func toggleStorageMethod() {
        let newMethod: APIKeyStorageMethod = storageMethod == .keychain ? .userDefaults : .keychain
        
        // Check keychain accessibility if switching to keychain (only access keychain when actually needed)
        if newMethod == .keychain && storageMethod != .keychain && !SecureAPIKeyStorage.shared.isKeychainAccessible() {
            showStorageError = true
            storageErrorMessage = "Keychain is not accessible. Please ensure your device is unlocked and try again."
            
            // Hide error after 5 seconds
            DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                showStorageError = false
            }
            return
        }
        
        // Clear any previous error
        showStorageError = false
        
        // Start migration
        isMigrating = true
        
        Task { @MainActor in
            do {
                // Use the single access point for migration
                let migrationResults: [LLMProvider: Bool]
                
                switch newMethod {
                case .keychain:
                    migrationResults = SecureAPIKeyStorage.shared.migrateAllToKeychain()
                case .userDefaults:
                    migrationResults = SecureAPIKeyStorage.shared.migrateAllToUserDefaults()
                }
                
                isMigrating = false
                
                let failedMigrations = migrationResults.filter { !$0.value }
                
                if failedMigrations.isEmpty {
                    // All migrations successful
                    storageMethod = newMethod
                    
                    let migratedCount = migrationResults.count
                    PotterLogger.shared.info("api_storage", "✅ Successfully migrated \(migratedCount) API keys to \(newMethod.rawValue)")
                    
                    // Show brief success message
                    showingSuccessCheckmark = true
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                        showingSuccessCheckmark = false
                    }
                } else {
                    // Some migrations failed
                    showStorageError = true
                    storageErrorMessage = "Failed to migrate \(failedMigrations.count) API key(s) to \(newMethod.displayName). Please try again."
                    
                    // Hide error after 7 seconds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 7) {
                        showStorageError = false
                    }
                }
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

// MARK: - Preview
struct LLMProviderView_Previews: PreviewProvider {
    static var previews: some View {
        LLMProviderView()
            .frame(width: 600, height: 400)
            .padding()
    }
}