import AppKit
import Foundation

class SimpleSettingsWindowController: NSWindowController {
    static let shared = SimpleSettingsWindowController()
    
    private init() {
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 500, height: 300),
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        
        super.init(window: window)
        
        window.title = "Potter Settings"
        window.center()
        window.isReleasedWhenClosed = false
        
        setupWindowContent()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setupWindowContent() {
        guard let window = window else { return }
        
        let contentView = NSView(frame: window.contentRect(forFrameRect: window.frame))
        window.contentView = contentView
        
        // Header label
        let headerLabel = NSTextField(labelWithString: "🎭 Potter Settings")
        headerLabel.font = NSFont.systemFont(ofSize: 20, weight: .semibold)
        headerLabel.frame = NSRect(x: 20, y: 240, width: 460, height: 30)
        contentView.addSubview(headerLabel)
        
        // API Key section
        let apiKeyLabel = NSTextField(labelWithString: "OpenAI API Key:")
        apiKeyLabel.frame = NSRect(x: 20, y: 200, width: 120, height: 20)
        contentView.addSubview(apiKeyLabel)
        
        let apiKeyField = NSSecureTextField(frame: NSRect(x: 150, y: 200, width: 280, height: 22))
        apiKeyField.placeholderString = "sk-..."
        
        // Load existing API key
        if let savedKey = UserDefaults.standard.string(forKey: "openai_api_key") {
            apiKeyField.stringValue = savedKey
        }
        
        contentView.addSubview(apiKeyField)
        
        // Processing modes info
        let modesLabel = NSTextField(labelWithString: "Available Processing Modes:")
        modesLabel.frame = NSRect(x: 20, y: 160, width: 200, height: 20)
        contentView.addSubview(modesLabel)
        
        let modesInfo = NSTextField(wrappingLabelWithString: """
        • Summarize - Creates concise summaries
        • Make Formal - Converts to professional tone
        • Make Casual - Converts to relaxed tone
        
        Use the menu bar to switch between modes.
        """)
        modesInfo.frame = NSRect(x: 20, y: 80, width: 460, height: 80)
        contentView.addSubview(modesInfo)
        
        // Buttons
        let saveButton = NSButton(title: "Save & Close", target: self, action: #selector(saveAndClose))
        saveButton.frame = NSRect(x: 350, y: 20, width: 120, height: 32)
        saveButton.bezelStyle = .rounded
        contentView.addSubview(saveButton)
        
        let testButton = NSButton(title: "Test API Key", target: self, action: #selector(testAPIKey))
        testButton.frame = NSRect(x: 220, y: 20, width: 120, height: 32)
        testButton.bezelStyle = .rounded
        contentView.addSubview(testButton)
        
        // Store reference to the API key field so we can access it later
        window.contentView?.viewWithTag(100)?.removeFromSuperview() // Remove if exists
        apiKeyField.tag = 100
    }
    
    @objc private func saveAndClose() {
        guard let window = window,
              let apiKeyField = window.contentView?.viewWithTag(100) as? NSTextField else {
            return
        }
        
        let apiKey = apiKeyField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        
        if !apiKey.isEmpty {
            UserDefaults.standard.set(apiKey, forKey: "openai_api_key")
            print("✅ API key saved")
            
            let alert = NSAlert()
            alert.messageText = "Settings Saved"
            alert.informativeText = "Your API key has been saved successfully."
            alert.addButton(withTitle: "OK")
            alert.runModal()
        }
        
        close()
    }
    
    @objc private func testAPIKey() {
        guard let window = window,
              let apiKeyField = window.contentView?.viewWithTag(100) as? NSTextField else {
            return
        }
        
        let apiKey = apiKeyField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        
        guard !apiKey.isEmpty else {
            let alert = NSAlert()
            alert.messageText = "No API Key"
            alert.informativeText = "Please enter an API key first."
            alert.addButton(withTitle: "OK")
            alert.runModal()
            return
        }
        
        // Simple test - just check if it looks like a valid OpenAI key
        if apiKey.hasPrefix("sk-") && apiKey.count > 10 {
            let alert = NSAlert()
            alert.messageText = "API Key Format Valid"
            alert.informativeText = "Your API key format looks correct. To fully test it, try processing some text."
            alert.addButton(withTitle: "OK")
            alert.runModal()
        } else {
            let alert = NSAlert()
            alert.messageText = "Invalid API Key Format"
            alert.informativeText = "OpenAI API keys typically start with 'sk-' and are longer."
            alert.addButton(withTitle: "OK")
            alert.runModal()
        }
    }
    
    override func showWindow(_ sender: Any?) {
        super.showWindow(sender)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}