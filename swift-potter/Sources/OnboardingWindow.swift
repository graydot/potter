import SwiftUI
import AppKit

class OnboardingWindowController: NSWindowController {
    static let shared = OnboardingWindowController()
    
    private init() {
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 600, height: 500),
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        
        super.init(window: window)
        
        window.title = "Welcome to Potter"
        window.center()
        window.isReleasedWhenClosed = false
        window.contentView = NSHostingView(rootView: OnboardingView())
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    func showOnboarding() {
        // Reset to first step when reopened
        if let hostingView = window?.contentView as? NSHostingView<OnboardingView> {
            hostingView.rootView.resetToFirstStep()
        }
        showWindow(nil)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

struct OnboardingView: View {
    @State private var currentStep = 0
    private let totalSteps = 5
    
    var body: some View {
        VStack(spacing: 30) {
            // Header
            VStack(spacing: 10) {
                Image(systemName: "wand.and.stars")
                    .font(.system(size: 48))
                    .foregroundColor(.blue)
                
                Text("Welcome to Potter")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("AI-powered text enhancement in 5 easy steps")
                    .font(.headline)
                    .foregroundColor(.secondary)
            }
            .padding(.top, 20)
            
            // Step content
            VStack(spacing: 20) {
                stepContent
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .padding(.horizontal, 40)
            
            // Navigation
            HStack {
                if currentStep > 0 {
                    Button("Back") {
                        currentStep -= 1
                    }
                    .keyboardShortcut(.leftArrow, modifiers: [])
                }
                
                Spacer()
                
                // Step indicator
                HStack(spacing: 8) {
                    ForEach(0..<totalSteps, id: \.self) { step in
                        Circle()
                            .fill(step <= currentStep ? Color.blue : Color.gray.opacity(0.3))
                            .frame(width: 10, height: 10)
                    }
                }
                
                Spacer()
                
                if currentStep < totalSteps - 1 {
                    Button("Next") {
                        currentStep += 1
                    }
                    .keyboardShortcut(.rightArrow, modifiers: [])
                    .keyboardShortcut(.return, modifiers: [])
                } else {
                    Button("Get Started") {
                        completeOnboarding()
                    }
                    .keyboardShortcut(.return, modifiers: [])
                    .buttonStyle(.borderedProminent)
                }
            }
            .padding(.horizontal, 40)
            .padding(.bottom, 30)
        }
        .frame(width: 600, height: 500)
    }
    
    @ViewBuilder
    private var stepContent: some View {
        switch currentStep {
        case 0:
            stepView(
                icon: "key.fill",
                title: "1. Add Your API Key",
                description: "Choose your AI provider (OpenAI, Anthropic, or Google) and add your API key in Settings.",
                note: "Potter works with multiple AI providers - pick your favorite!"
            )
            
        case 1:
            stepView(
                icon: "doc.on.clipboard",
                title: "2. Copy Text",
                description: "Select and copy any text you want to enhance - emails, documents, messages, anything!",
                note: "Potter works with text from any app on your Mac."
            )
            
        case 2:
            stepView(
                icon: "command",
                title: "3. Use the Magic Shortcut",
                description: "Press ⌘+⇧+9 anywhere on your Mac to instantly enhance your copied text.",
                note: "The shortcut works globally - no need to switch apps!"
            )
            
        case 3:
            stepView(
                icon: "arrow.down.doc",
                title: "4. Paste Enhanced Text",
                description: "Your enhanced text is automatically copied back to clipboard. Just paste it wherever you need it!",
                note: "⌘+V to paste your improved text."
            )
            
        case 4:
            stepView(
                icon: "sparkles",
                title: "5. Explore More Prompts",
                description: "Try different enhancement styles: Polish, Summarize, Elaborate, Make Formal, or add your own custom prompts!",
                note: "Access all prompts from the menu bar or create custom ones in Settings."
            )
            
        default:
            EmptyView()
        }
    }
    
    private func stepView(icon: String, title: String, description: String, note: String) -> some View {
        VStack(spacing: 20) {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundColor(.blue)
            
            Text(title)
                .font(.title2)
                .fontWeight(.semibold)
            
            Text(description)
                .font(.body)
                .multilineTextAlignment(.center)
                .lineLimit(nil)
            
            HStack {
                Image(systemName: "lightbulb")
                    .foregroundColor(.orange)
                Text(note)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 8)
            .background(Color.orange.opacity(0.1))
            .cornerRadius(8)
        }
    }
    
    private func completeOnboarding() {
        // Mark onboarding as completed
        UserDefaults.standard.set(true, forKey: "onboarding_completed")
        
        // Close onboarding window
        OnboardingWindowController.shared.window?.close()
        
        // Open settings to start API key setup
        ModernSettingsWindowController.shared.showWindow(nil)
    }
    
    func resetToFirstStep() {
        currentStep = 0
    }
}