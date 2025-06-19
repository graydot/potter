import AppKit
import Foundation

// MARK: - Custom Window for Key Handling
class PromptEditWindow: NSWindow {
    weak var dialogController: PromptEditDialogController?
    
    override func keyDown(with event: NSEvent) {
        print("🔑 Window keyDown: keyCode=\(event.keyCode), chars='\(event.characters ?? "")'")
        
        // Handle Escape key
        if event.keyCode == 53 {
            print("⌨️ Escape key in window")
            dialogController?.cancelClicked()
            return
        }
        
        // Handle Return key
        if event.keyCode == 36 {
            print("⌨️ Return key in window")
            dialogController?.saveClicked()
            return
        }
        
        super.keyDown(with: event)
    }
}


// MARK: - Prompt Edit Dialog Controller
class PromptEditDialogController: NSWindowController {
    
    // MARK: - Properties
    private let isEditing: Bool
    private let existingPrompt: PromptItem?
    private let existingPromptNames: [String]
    
    // UI Components
    private var nameTextField: NSTextField!
    private var promptTextView: NSTextView!
    private var nameCharCountLabel: NSTextField!
    private var promptCharCountLabel: NSTextField!
    private var validationLabel: NSTextField!
    private var saveButton: NSButton!
    private var cancelButton: NSButton!
    
    // Validation state
    private var isValidInput: Bool = false
    
    // Callback
    var onSave: ((String, String) -> Void)?
    
    // MARK: - Initialization
    init(isEditing: Bool, existingPrompt: PromptItem?, existingPromptNames: [String]) {
        self.isEditing = isEditing
        self.existingPrompt = existingPrompt
        self.existingPromptNames = existingPromptNames
        
        // Create custom window with key handling
        let window = PromptEditWindow(
            contentRect: NSRect(x: 0, y: 0, width: 500, height: 400),
            styleMask: [.titled, .closable],
            backing: .buffered,
            defer: false
        )
        
        super.init(window: window)
        
        // Connect the window to this controller
        (window as? PromptEditWindow)?.dialogController = self
        
        setupWindow()
        setupUI()
        setupMenuCommands()
        loadExistingData()
        validateInput()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    // MARK: - Menu Commands Setup
    private func setupMenuCommands() {
        // This will ensure standard editing commands work
        // The responder chain should handle these automatically
    }
    
    // MARK: - Window Setup
    private func setupWindow() {
        guard let window = window else { return }
        
        window.title = isEditing ? "Edit Prompt" : "New Prompt"
        window.isReleasedWhenClosed = false
        window.center()
        
        // Ensure window accepts mouse events
        window.acceptsMouseMovedEvents = true
    }
    
    // MARK: - UI Setup
    private func setupUI() {
        guard let window = window else { return }
        
        let contentView = NSView(frame: window.contentView!.bounds)
        window.contentView = contentView
        
        // Title label
        let titleLabel = NSTextField(labelWithString: isEditing ? "Edit Prompt" : "New Prompt")
        titleLabel.font = NSFont.boldSystemFont(ofSize: 16)
        titleLabel.alignment = .center
        
        // Name section
        let nameLabel = NSTextField(labelWithString: "Name:")
        nameLabel.font = NSFont.boldSystemFont(ofSize: 13)
        
        nameCharCountLabel = NSTextField(labelWithString: "0/50")
        nameCharCountLabel.font = NSFont.systemFont(ofSize: 11)
        nameCharCountLabel.textColor = .secondaryLabelColor
        nameCharCountLabel.alignment = .right
        
        nameTextField = NSTextField()
        nameTextField.placeholderString = "Enter prompt name"
        nameTextField.target = self
        nameTextField.action = #selector(nameTextChanged)
        nameTextField.isEditable = true
        nameTextField.isSelectable = true
        
        // Prompt section
        let promptLabel = NSTextField(labelWithString: "Prompt:")
        promptLabel.font = NSFont.boldSystemFont(ofSize: 13)
        
        promptCharCountLabel = NSTextField(labelWithString: "0/5000")
        promptCharCountLabel.font = NSFont.systemFont(ofSize: 11)
        promptCharCountLabel.textColor = .secondaryLabelColor
        promptCharCountLabel.alignment = .right
        
        // Text view with scroll view
        let scrollView = NSScrollView()
        scrollView.hasVerticalScroller = true
        scrollView.hasHorizontalScroller = false
        scrollView.autohidesScrollers = true
        scrollView.borderType = .bezelBorder
        
        promptTextView = NSTextView()
        promptTextView.isEditable = true
        promptTextView.isSelectable = true
        promptTextView.allowsUndo = true
        promptTextView.font = NSFont.systemFont(ofSize: 13)
        promptTextView.delegate = self
        promptTextView.string = ""
        promptTextView.isRichText = false
        promptTextView.isAutomaticQuoteSubstitutionEnabled = false
        promptTextView.isAutomaticDashSubstitutionEnabled = false
        promptTextView.isAutomaticTextReplacementEnabled = false
        
        // Proper text container setup for NSTextView
        promptTextView.isVerticallyResizable = true
        promptTextView.isHorizontallyResizable = false
        promptTextView.autoresizingMask = [.width]
        
        // Configure text container after it's created
        if let textContainer = promptTextView.textContainer {
            textContainer.containerSize = NSSize(width: 460, height: CGFloat.greatestFiniteMagnitude) // Fixed width for now
            textContainer.widthTracksTextView = true
        }
        
        scrollView.documentView = promptTextView
        
        // Validation label
        validationLabel = NSTextField(labelWithString: "")
        validationLabel.font = NSFont.systemFont(ofSize: 11)
        validationLabel.textColor = .systemRed
        validationLabel.isHidden = true
        
        // Buttons
        cancelButton = NSButton(title: "Cancel", target: self, action: #selector(cancelClicked))
        cancelButton.bezelStyle = .rounded
        
        saveButton = NSButton(title: "Save", target: self, action: #selector(saveClicked))
        saveButton.bezelStyle = .rounded
        saveButton.isEnabled = false
        
        // Debug button setup
        print("🔘 Button setup - Cancel target: \(String(describing: cancelButton.target)), action: \(String(describing: cancelButton.action))")
        print("🔘 Button setup - Save target: \(String(describing: saveButton.target)), action: \(String(describing: saveButton.action))")
        
        // Make save button prominent
        if #available(macOS 11.0, *) {
            saveButton.hasDestructiveAction = false
            saveButton.controlSize = .regular
        }
        
        // Layout using Auto Layout
        contentView.addSubview(titleLabel)
        contentView.addSubview(nameLabel)
        contentView.addSubview(nameCharCountLabel)
        contentView.addSubview(nameTextField)
        contentView.addSubview(promptLabel)
        contentView.addSubview(promptCharCountLabel)
        contentView.addSubview(scrollView)
        contentView.addSubview(validationLabel)
        contentView.addSubview(cancelButton)
        contentView.addSubview(saveButton)
        
        // Disable autoresizing masks
        [titleLabel, nameLabel, nameCharCountLabel, nameTextField, promptLabel, promptCharCountLabel, scrollView, validationLabel, cancelButton, saveButton].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
        }
        
        // Setup constraints
        NSLayoutConstraint.activate([
            // Title
            titleLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 20),
            titleLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            
            // Name section
            nameLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 20),
            nameLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            
            nameCharCountLabel.topAnchor.constraint(equalTo: nameLabel.topAnchor),
            nameCharCountLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            nameTextField.topAnchor.constraint(equalTo: nameLabel.bottomAnchor, constant: 5),
            nameTextField.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            nameTextField.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // Prompt section
            promptLabel.topAnchor.constraint(equalTo: nameTextField.bottomAnchor, constant: 20),
            promptLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            
            promptCharCountLabel.topAnchor.constraint(equalTo: promptLabel.topAnchor),
            promptCharCountLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            scrollView.topAnchor.constraint(equalTo: promptLabel.bottomAnchor, constant: 5),
            scrollView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            scrollView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            scrollView.heightAnchor.constraint(equalToConstant: 150),
            
            // Validation label
            validationLabel.topAnchor.constraint(equalTo: scrollView.bottomAnchor, constant: 5),
            validationLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            validationLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // Buttons
            cancelButton.topAnchor.constraint(equalTo: validationLabel.bottomAnchor, constant: 20),
            cancelButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            cancelButton.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20),
            
            saveButton.topAnchor.constraint(equalTo: cancelButton.topAnchor),
            saveButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            saveButton.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20)
        ])
    }
    
    // MARK: - Data Loading
    private func loadExistingData() {
        if let existing = existingPrompt {
            print("📝 Loading existing prompt: '\(existing.name)' with \(existing.prompt.count) characters")
            nameTextField.stringValue = existing.name
            promptTextView.string = existing.prompt
            
            // Force layout and refresh
            DispatchQueue.main.async {
                self.window?.layoutIfNeeded()
                self.promptTextView.needsDisplay = true
                print("📝 After layout - Text view frame: \(self.promptTextView.frame)")
            }
            
            updateCharacterCounts()
            print("📝 Text view now contains: '\(promptTextView.string.prefix(50))...' (\(promptTextView.string.count) chars)")
            print("📝 Text view frame: \(promptTextView.frame)")
            print("📝 Text view is editable: \(promptTextView.isEditable), selectable: \(promptTextView.isSelectable)")
        } else {
            print("📝 No existing prompt to load - creating new")
        }
    }
    
    // MARK: - Validation
    private func validateInput() {
        let trimmedName = nameTextField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedPrompt = promptTextView.string.trimmingCharacters(in: .whitespacesAndNewlines)
        
        var validationMessage = ""
        
        // Check for empty name
        if trimmedName.isEmpty {
            validationMessage = "Name cannot be empty"
        }
        // Check name length
        else if trimmedName.count > 50 {
            validationMessage = "Name cannot exceed 50 characters"
        }
        // Check for duplicate names (excluding current prompt when editing)
        else if trimmedName != (existingPrompt?.name ?? "") && existingPromptNames.contains(trimmedName) {
            validationMessage = "A prompt with this name already exists"
        }
        // Check for empty prompt
        else if trimmedPrompt.isEmpty {
            validationMessage = "Prompt text cannot be empty"
        }
        // Check prompt length
        else if trimmedPrompt.count > 5000 {
            validationMessage = "Prompt text cannot exceed 5000 characters"
        }
        
        // Update validation display
        if validationMessage.isEmpty {
            validationLabel.isHidden = true
            isValidInput = true
        } else {
            validationLabel.stringValue = validationMessage
            validationLabel.isHidden = false
            isValidInput = false
        }
        
        saveButton.isEnabled = isValidInput
        updateCharacterCounts()
        
        print("📋 Validation: name='\(trimmedName)' (\(trimmedName.count) chars), prompt='\(trimmedPrompt.prefix(20))...' (\(trimmedPrompt.count) chars), valid=\(isValidInput), message='\(validationMessage)'")
    }
    
    private func updateCharacterCounts() {
        let nameCount = nameTextField.stringValue.count
        let promptCount = promptTextView.string.count
        
        nameCharCountLabel.stringValue = "\(nameCount)/50"
        nameCharCountLabel.textColor = nameCount > 50 ? .systemRed : .secondaryLabelColor
        
        promptCharCountLabel.stringValue = "\(promptCount)/5000"
        promptCharCountLabel.textColor = promptCount > 5000 ? .systemRed : .secondaryLabelColor
    }
    
    // MARK: - Actions
    @objc private func nameTextChanged() {
        validateInput()
    }
    
    @objc func saveClicked() {
        print("💾 Save button clicked! Valid input: \(isValidInput)")
        guard isValidInput else { 
            print("💾 Cannot save - validation failed")
            return 
        }
        
        let trimmedName = nameTextField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedPrompt = promptTextView.string.trimmingCharacters(in: .whitespacesAndNewlines)
        
        print("💾 Saving prompt: '\(trimmedName)' with \(trimmedPrompt.count) characters")
        onSave?(trimmedName, trimmedPrompt)
        close()
    }
    
    @objc func cancelClicked() {
        print("❌ Cancel button clicked!")
        close()
    }
    
    // Override window's key event handling
    override func windowDidLoad() {
        super.windowDidLoad()
        
        // Set up window to handle key events
        window?.acceptsMouseMovedEvents = true
    }
    
    // MARK: - Modal Presentation
    func showModal() {
        guard let window = window else { return }
        
        // Show as a regular window
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        
        // Simple focus - just set the initial key view
        window.initialFirstResponder = nameTextField
        window.makeFirstResponder(nameTextField)
    }
    
    override func close() {
        super.close()
    }
}

// MARK: - NSTextViewDelegate
extension PromptEditDialogController: NSTextViewDelegate {
    func textDidChange(_ notification: Notification) {
        validateInput()
    }
}