import SwiftUI
import AppKit

// MARK: - LLM Provider Configuration View
struct LLMProviderView: View {
    @StateObject private var viewModel = LLMProviderViewModel()
    
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
        .onChange(of: viewModel.selectedProvider) { newProvider in
            viewModel.onProviderChanged(to: newProvider)
        }
    }
    
    
    // MARK: - Provider Selection
    private var providerSelectionView: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Provider:")
                    .fontWeight(.medium)
                    .frame(width: 80, alignment: .leading)
                
                Picker("", selection: $viewModel.selectedProvider) {
                    ForEach(LLMProvider.allCases) { provider in
                        Text(provider.displayName)
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
                
                Picker("", selection: $viewModel.selectedModel) {
                    ForEach(viewModel.selectedProvider.models) { model in
                        Text(model.name)
                            .tag(model as LLMModel?)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                .frame(width: 200)
                .help(viewModel.selectedModel?.description ?? "Select a model")
                
                Spacer()
            }
            
            // Description text below the picker
            if let selectedModel = viewModel.selectedModel {
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
            if case .invalid(let message) = viewModel.currentValidationState {
                Text(message)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding(.leading, 88) // Align with API key field
            }
            
            // Storage Error Message
            if viewModel.showStorageError {
                Text(viewModel.storageErrorMessage)
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
                    viewModel.openAPIKeyURL()
                }) {
                    Text(viewModel.selectedProvider.displayName + " API Keys")
                        .font(.caption)
                        .foregroundColor(.blue)
                        .underline()
                }
                .buttonStyle(.plain)
                .help("Open \(viewModel.selectedProvider.displayName) API keys page in browser")
            }
            .padding(.leading, 88) // Align with API key field
            
            // Storage Method Status with Success Message on same line
            HStack(spacing: 6) {
                Text("Storage:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .fixedSize()
                
                Text(viewModel.storageStatusText)
                    .font(.caption)
                    .foregroundColor(viewModel.storageStatusColor)
                    .fontWeight(.medium)
                    .lineLimit(1)
                
                Image(systemName: viewModel.storageIcon)
                    .font(.caption)
                    .foregroundColor(viewModel.storageStatusColor)
                
                // Success Message on the same line, to the right
                if viewModel.showingSuccessCheckmark {
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
            if viewModel.showAPIKey {
                TextField(viewModel.selectedProvider.apiKeyPlaceholder, text: $viewModel.apiKeyText)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(.body, design: .monospaced))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(viewModel.textFieldBorderColor, lineWidth: 2)
                    )
            } else {
                SecureField(viewModel.selectedProvider.apiKeyPlaceholder, text: $viewModel.apiKeyText)
                    .textFieldStyle(.roundedBorder)
                    .font(.system(.body, design: .monospaced))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(viewModel.textFieldBorderColor, lineWidth: 2)
                    )
            }
            
            Button(action: {
                viewModel.toggleAPIKeyVisibility()
            }) {
                Image(systemName: viewModel.showAPIKey ? "eye.slash" : "eye")
                    .foregroundColor(.secondary)
            }
            .buttonStyle(.plain)
            .help(viewModel.showAPIKey ? "Hide API key" : "Show API key")
        }
        .frame(width: 300)
        .onChange(of: viewModel.apiKeyText) { newValue in
            viewModel.onAPIKeyTextChanged(newValue)
        }
    }
    
    
    private var validationStatusView: some View {
        Group {
            switch viewModel.currentValidationState {
            case .some(.validating):
                ProgressView()
                    .scaleEffect(0.7)
                    .frame(width: 20, height: 20)
                
            default:
                EmptyView()
            }
        }
        .frame(width: 24, height: 20)
    }
    
    private var testAndSaveButton: some View {
        Button("Test & Save") {
            Task {
                await viewModel.testAndSaveAPIKey()
            }
        }
        .buttonStyle(.borderedProminent)
        .disabled(viewModel.isTestAndSaveButtonDisabled)
    }
    
    private var storageMethodToggle: some View {
        Button(action: {
            Task {
                await viewModel.toggleStorageMethod()
            }
        }) {
            if viewModel.isMigrating {
                ProgressView()
                    .scaleEffect(0.7)
                    .frame(width: 24, height: 20)
            } else {
                Image(systemName: viewModel.storageIcon)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(viewModel.storageStatusColor)
                    .frame(width: 24, height: 20)
            }
        }
        .buttonStyle(.plain)
        .disabled(viewModel.isMigrating)
        .help(viewModel.storageToggleHelp)
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