import AppKit
import Foundation

// MARK: - Drag Handle View

/// A subtle horizontal bar below the prompt text area that the user can drag
/// to resize the text area. Shows a resize cursor on hover.
private final class DragHandleView: NSView {

    /// Called continuously during drag with the new desired height for the scroll view.
    var onHeightChange: ((CGFloat) -> Void)?
    /// Called once when the drag ends so the final value can be persisted.
    var onHeightCommit: ((CGFloat) -> Void)?

    private var dragStartY: CGFloat = 0
    private var dragStartHeight: CGFloat = 0

    /// The current height of the scroll view at the time the drag begins.
    var currentScrollViewHeight: CGFloat = 150

    // MARK: Appearance

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)

        // Subtle pill / grip indicator centred in the handle strip
        let pillW: CGFloat = 32
        let pillH: CGFloat = 4
        let pillX = (bounds.width - pillW) / 2
        let pillY = (bounds.height - pillH) / 2
        let pill = NSBezierPath(roundedRect: NSRect(x: pillX, y: pillY, width: pillW, height: pillH),
                                xRadius: 2, yRadius: 2)
        NSColor.tertiaryLabelColor.setFill()
        pill.fill()
    }

    // MARK: Cursor

    override func resetCursorRects() {
        addCursorRect(bounds, cursor: .resizeUpDown)
    }

    // MARK: Drag

    override func mouseDown(with event: NSEvent) {
        dragStartY = convert(event.locationInWindow, from: nil).y
        dragStartHeight = currentScrollViewHeight
    }

    override func mouseDragged(with event: NSEvent) {
        let currentY = convert(event.locationInWindow, from: nil).y
        // Dragging down (negative delta in flipped coords) makes the view taller.
        // NSView uses bottom-left origin, so moving down = smaller Y = taller text area.
        let delta = dragStartY - currentY
        let newHeight = max(80, dragStartHeight + delta)
        onHeightChange?(newHeight)
    }

    override func mouseUp(with event: NSEvent) {
        let currentY = convert(event.locationInWindow, from: nil).y
        let delta = dragStartY - currentY
        let finalHeight = max(80, dragStartHeight + delta)
        onHeightCommit?(finalHeight)
    }
}

// MARK: - Custom Window for Key Handling
class PromptEditWindow: NSWindow {
    weak var dialogController: PromptEditDialogController?
    
    override var canBecomeKey: Bool {
        return true
    }
    
    override var canBecomeMain: Bool {
        return true
    }
    
    override func keyDown(with event: NSEvent) {
        print("🔑 Window keyDown: keyCode=\(event.keyCode), chars='\(event.characters ?? "")'")
        
        // Handle Escape key
        if event.keyCode == 53 {
            print("⌨️ Escape key in window")
            if let controller = dialogController {
                controller.cancelClicked(NSButton()) // Create dummy button for call
            }
            return
        }
        
        // Handle Cmd+Return for Save
        if event.keyCode == 36 && event.modifierFlags.contains(.command) {
            print("⌨️ Cmd+Return key in window")
            if let controller = dialogController {
                controller.saveClicked(NSButton()) // Create dummy button for call
            }
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
    private var tierPopUp: NSPopUpButton!
    private var outputModeSegment: NSSegmentedControl!
    private var validationLabel: NSTextField!
    private var saveButton: NSButton!
    private var cancelButton: NSButton!
    private var dragHandle: DragHandleView!
    private var scrollViewHeightConstraint: NSLayoutConstraint!

    // Validation state
    private var isValidInput: Bool = false

    // Callback: name, prompt, modelTier, outputMode
    var onSave: ((String, String, ModelTier?, OutputMode) -> Void)?
    
    // Event monitor for proper cleanup
    private var eventMonitor: Any?
    
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
        window.dialogController = self
        
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
        nameTextField.delegate = self
        
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

        // Model tier section
        let tierLabel = NSTextField(labelWithString: "Model Tier:")
        tierLabel.font = NSFont.boldSystemFont(ofSize: 13)

        tierPopUp = NSPopUpButton()
        tierPopUp.addItem(withTitle: "Default (use global setting)")
        tierPopUp.lastItem?.tag = -1
        for tier in ModelTier.allCases {
            tierPopUp.addItem(withTitle: tier.displayName)
            tierPopUp.lastItem?.tag = ModelTier.allCases.firstIndex(of: tier)!
        }

        // Output mode section
        outputModeSegment = NSSegmentedControl(
            labels: OutputMode.allCases.map { $0.displayName },
            trackingMode: .selectOne,
            target: nil,
            action: nil
        )
        outputModeSegment.selectedSegment = 0  // default: Replace

        // Drag handle
        dragHandle = DragHandleView()
        dragHandle.wantsLayer = true
        dragHandle.layer?.backgroundColor = NSColor.windowBackgroundColor.cgColor

        // Wire drag handle callbacks
        dragHandle.onHeightChange = { [weak self] newHeight in
            guard let self = self else { return }
            self.scrollViewHeightConstraint.constant = newHeight
            self.dragHandle.currentScrollViewHeight = newHeight
            // Grow/shrink the window to accommodate the new text area size.
            self.resizeWindowForCurrentConstraints()
        }
        dragHandle.onHeightCommit = { finalHeight in
            UIStateStore.shared.promptTextAreaHeight = finalHeight
            print("📐 Prompt text area height committed: \(finalHeight)pt")
        }

        // Validation label
        validationLabel = NSTextField(labelWithString: "")
        validationLabel.font = NSFont.systemFont(ofSize: 11)
        validationLabel.textColor = .systemRed
        validationLabel.isHidden = true

        // Buttons
        cancelButton = NSButton(title: "Cancel", target: self, action: #selector(cancelClicked(_:)))
        cancelButton.bezelStyle = .rounded

        saveButton = NSButton(title: "Save", target: self, action: #selector(saveClicked(_:)))
        saveButton.bezelStyle = .rounded
        saveButton.isEnabled = false

        // Debug button setup
        print("🔘 Button setup - Cancel target: \(String(describing: cancelButton.target)), action: \(String(describing: cancelButton.action))")
        print("🔘 Button setup - Save target: \(String(describing: saveButton.target)), action: \(String(describing: saveButton.action))")

        // Test if buttons are responsive
        cancelButton.isEnabled = true

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
        contentView.addSubview(dragHandle)
        contentView.addSubview(tierLabel)
        contentView.addSubview(tierPopUp)
        contentView.addSubview(outputModeSegment)
        contentView.addSubview(validationLabel)
        contentView.addSubview(cancelButton)
        contentView.addSubview(saveButton)

        // Disable autoresizing masks
        [titleLabel, nameLabel, nameCharCountLabel, nameTextField, promptLabel, promptCharCountLabel,
         scrollView, dragHandle, tierLabel, tierPopUp, outputModeSegment, validationLabel,
         cancelButton, saveButton].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
        }

        // Determine initial text area height:
        //   • If the user previously set a height, use it.
        //   • Otherwise default to 25% of the window's content height (~400pt window → 100pt).
        let stored = UIStateStore.shared.promptTextAreaHeight
        let initialHeight: CGFloat = stored > 0 ? CGFloat(stored) : max(80, window.contentView!.bounds.height * 0.25)
        dragHandle.currentScrollViewHeight = initialHeight

        // Create the mutable height constraint so the drag handle can update it live.
        scrollViewHeightConstraint = scrollView.heightAnchor.constraint(equalToConstant: initialHeight)

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
            scrollViewHeightConstraint,

            // Drag handle — 12pt tall strip immediately below the scroll view
            dragHandle.topAnchor.constraint(equalTo: scrollView.bottomAnchor),
            dragHandle.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            dragHandle.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            dragHandle.heightAnchor.constraint(equalToConstant: 12),

            // Model tier
            tierLabel.topAnchor.constraint(equalTo: dragHandle.bottomAnchor, constant: 12),
            tierLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),

            tierPopUp.centerYAnchor.constraint(equalTo: tierLabel.centerYAnchor),
            tierPopUp.leadingAnchor.constraint(equalTo: tierLabel.trailingAnchor, constant: 8),
            tierPopUp.widthAnchor.constraint(equalToConstant: 250),

            // Output mode
            outputModeSegment.topAnchor.constraint(equalTo: tierLabel.bottomAnchor, constant: 12),
            outputModeSegment.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),

            // Validation label
            validationLabel.topAnchor.constraint(equalTo: outputModeSegment.bottomAnchor, constant: 5),
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
    
    // MARK: - Window Resize Helpers

    /// Re-sizes the window so that all Auto Layout constraints are satisfied after
    /// the drag-handle changes the text area height. The window expands or contracts
    /// from its top edge so that on-screen position feels stable.
    private func resizeWindowForCurrentConstraints() {
        guard let window = window, let contentView = window.contentView else { return }

        // Ask Auto Layout what size the content view needs right now.
        let fittingSize = contentView.fittingSize
        let newContentHeight = max(fittingSize.height, 300)

        var frame = window.frame
        let oldHeight = frame.height
        let newWindowHeight = newContentHeight + (window.frame.height - (window.contentView?.frame.height ?? 0))
        // Adjust origin.y to keep the window's top edge fixed.
        frame.origin.y += (oldHeight - newWindowHeight)
        frame.size.height = newWindowHeight
        window.setFrame(frame, display: true, animate: false)
    }

    // MARK: - Data Loading
    private func loadExistingData() {
        if let existing = existingPrompt {
            print("📝 Loading existing prompt: '\(existing.name)' with \(existing.prompt.count) characters")
            nameTextField.stringValue = existing.name
            promptTextView.string = existing.prompt

            // Set tier popup
            if let tier = existing.modelTier,
               let idx = ModelTier.allCases.firstIndex(of: tier) {
                tierPopUp.selectItem(at: idx + 1)  // +1 because index 0 is "Default"
            } else {
                tierPopUp.selectItem(at: 0)  // Default
            }

            // Set output mode segment
            if let modeIdx = OutputMode.allCases.firstIndex(of: existing.outputMode) {
                outputModeSegment.selectedSegment = modeIdx
            }
            
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
    
    @objc func saveClicked(_ sender: NSButton) {
        print("💾💾💾 SAVE BUTTON ACTUALLY CLICKED! 💾💾💾")
        print("💾 Save button clicked! Valid input: \(isValidInput)")
        guard isValidInput else { 
            print("💾 Cannot save - validation failed")
            return 
        }
        
        let trimmedName = nameTextField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedPrompt = promptTextView.string.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Resolve selected tier
        let selectedTierIndex = tierPopUp.indexOfSelectedItem
        let selectedTier: ModelTier? = selectedTierIndex > 0
            ? ModelTier.allCases[selectedTierIndex - 1]
            : nil

        // Resolve selected output mode
        let modeIdx = outputModeSegment.selectedSegment
        let selectedOutputMode: OutputMode = (modeIdx >= 0 && modeIdx < OutputMode.allCases.count)
            ? OutputMode.allCases[modeIdx]
            : .replace

        print("💾 Saving prompt: '\(trimmedName)' with \(trimmedPrompt.count) characters, tier: \(selectedTier?.displayName ?? "Default"), output: \(selectedOutputMode.displayName)")
        onSave?(trimmedName, trimmedPrompt, selectedTier, selectedOutputMode)
        close()
    }
    
    @objc func cancelClicked(_ sender: NSButton) {
        print("❌❌❌ CANCEL BUTTON ACTUALLY CLICKED! ❌❌❌")
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
        
        // Set up proper key event handling
        window.initialFirstResponder = nameTextField
        window.makeFirstResponder(nameTextField)
        
        // Add key monitoring for the window to catch ESC (with proper cleanup)
        eventMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            if event.keyCode == 53 { // ESC key
                print("🔑 Local monitor caught ESC key")
                self?.cancelClicked(NSButton())
                return nil // Consume the event
            }
            return event // Let other events pass through
        }
        
        // Debug button state after showing
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            print("🔍 Post-show button state:")
            print("  Cancel - enabled: \(self.cancelButton.isEnabled), superview: \(String(describing: self.cancelButton.superview))")
            print("  Save - enabled: \(self.saveButton.isEnabled), superview: \(String(describing: self.saveButton.superview))")
            print("  Window key: \(window.isKeyWindow), main: \(window.isMainWindow)")
        }
    }
    
    override func close() {
        // Clean up the event monitor to prevent interfering with other dialogs
        if let monitor = eventMonitor {
            NSEvent.removeMonitor(monitor)
            eventMonitor = nil
            print("🔑 Removed event monitor")
        }
        super.close()
    }
}

// MARK: - NSTextViewDelegate
extension PromptEditDialogController: NSTextViewDelegate {
    func textDidChange(_ notification: Notification) {
        validateInput()
    }
}

// MARK: - NSTextFieldDelegate  
extension PromptEditDialogController: NSTextFieldDelegate {
    func controlTextDidChange(_ obj: Notification) {
        validateInput()
    }
}