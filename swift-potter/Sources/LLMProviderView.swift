import SwiftUI
import AppKit

// MARK: - LLM Provider Configuration View
struct LLMProviderView: View {
    @StateObject private var llmManager = LLMManager()
    @State private var apiKeyText: String = ""
    @State private var showingSuccessCheckmark = false
    
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
            // Load current API key for display
            apiKeyText = llmManager.getAPIKey(for: llmManager.selectedProvider)
        }
        .onChange(of: llmManager.selectedProvider) { newProvider in
            // Load API key for the newly selected provider
            apiKeyText = llmManager.getAPIKey(for: newProvider)
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
            
            // Success Message
            if showingSuccessCheckmark {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    Text("API key saved successfully")
                        .font(.caption)
                        .foregroundColor(.green)
                }
                .padding(.leading, 88)
                .transition(.opacity)
            }
        }
    }
    
    private var apiKeyTextField: some View {
        SecureField(llmManager.selectedProvider.apiKeyPlaceholder, text: $apiKeyText)
            .textFieldStyle(RoundedBorderTextFieldStyle())
            .frame(width: 300)
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(textFieldBorderColor, lineWidth: 1)
            )
            .onChange(of: apiKeyText) { newValue in
                llmManager.setAPIKey(newValue, for: llmManager.selectedProvider)
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
            Task {
                await llmManager.validateAndSaveAPIKey(apiKeyText, for: llmManager.selectedProvider)
                
                // Show success checkmark briefly if validation succeeded
                if llmManager.validationStates[llmManager.selectedProvider]?.isValid == true {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        showingSuccessCheckmark = true
                    }
                    
                    DispatchQueue.main.asyncAfter(deadline: .now() + 3) {
                        withAnimation(.easeInOut(duration: 0.3)) {
                            showingSuccessCheckmark = false
                        }
                    }
                }
            }
        }
        .buttonStyle(.borderedProminent)
        .disabled(apiKeyText.isEmpty || llmManager.isValidating)
    }
}

// MARK: - Model Description Helper
// The description is now shown below the picker, so no additional components needed

// MARK: - Preview
struct LLMProviderView_Previews: PreviewProvider {
    static var previews: some View {
        LLMProviderView()
            .frame(width: 600, height: 400)
            .padding()
    }
}