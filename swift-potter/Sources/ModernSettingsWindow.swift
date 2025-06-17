import SwiftUI
import AppKit

extension DateFormatter {
    static let timeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        return formatter
    }()
}

// MARK: - Prompt Data Structure
struct PromptItem: Identifiable, Equatable, Codable {
    let id: UUID
    var name: String
    var prompt: String
    
    init(name: String, prompt: String) {
        self.id = UUID()
        self.name = name
        self.prompt = prompt
    }
    
    static func == (lhs: PromptItem, rhs: PromptItem) -> Bool {
        lhs.id == rhs.id
    }
}

// MARK: - Prompt Manager for Persistence
class PromptManager {
    static let shared = PromptManager()
    
    private var promptsFileURL: URL {
        if Bundle.main.bundleIdentifier != nil {
            // Production: Application Support
            let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            let potterDir = appSupport.appendingPathComponent("Potter")
            
            // Create directory if it doesn't exist
            try? FileManager.default.createDirectory(at: potterDir, withIntermediateDirectories: true)
            
            return potterDir.appendingPathComponent("prompts.json")
        } else {
            // Development: config/ directory
            let currentDir = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
            let configDir = currentDir.appendingPathComponent("config")
            
            // Create directory if it doesn't exist
            try? FileManager.default.createDirectory(at: configDir, withIntermediateDirectories: true)
            
            return configDir.appendingPathComponent("prompts.json")
        }
    }
    
    func loadPrompts() -> [PromptItem] {
        // Check if file exists, if not create it with defaults
        if !FileManager.default.fileExists(atPath: promptsFileURL.path) {
            let defaults = defaultPrompts()
            savePrompts(defaults)
            PotterLogger.shared.info("prompts", "📄 Created new prompts file with \(defaults.count) default prompts at \(promptsFileURL.path)")
            return defaults
        }
        
        // File exists, load from it
        do {
            let data = try Data(contentsOf: promptsFileURL)
            let prompts = try JSONDecoder().decode([PromptItem].self, from: data)
            PotterLogger.shared.info("prompts", "📖 Loaded \(prompts.count) prompts from \(promptsFileURL.path)")
            return prompts
        } catch {
            PotterLogger.shared.error("prompts", "📖 Failed to load prompts file: \(error.localizedDescription)")
            // If file is corrupted, recreate with defaults
            let defaults = defaultPrompts()
            savePrompts(defaults)
            PotterLogger.shared.info("prompts", "📄 Recreated corrupted prompts file with defaults")
            return defaults
        }
    }
    
    func savePrompts(_ prompts: [PromptItem]) {
        do {
            let data = try JSONEncoder().encode(prompts)
            try data.write(to: promptsFileURL)
            PotterLogger.shared.info("prompts", "💾 Saved \(prompts.count) prompts to \(promptsFileURL.path)")
        } catch {
            PotterLogger.shared.error("prompts", "💾 Failed to save prompts: \(error.localizedDescription)")
        }
    }
    
    private func defaultPrompts() -> [PromptItem] {
        return [
            PromptItem(name: "summarize", prompt: "Please provide a concise summary of the following text. Focus on the key points and main ideas while maintaining clarity and brevity."),
            PromptItem(name: "formal", prompt: "Please rewrite the following text in a formal, professional tone. Use proper business language and maintain a respectful, authoritative voice."),
            PromptItem(name: "casual", prompt: "Please rewrite the following text in a casual, relaxed tone. Make it sound conversational and friendly, as if talking to a friend."),
            PromptItem(name: "friendly", prompt: "Please rewrite the following text in a warm, friendly tone. Make it sound welcoming and approachable while maintaining professionalism."),
        ]
    }
}

// MARK: - Custom Window for ESC Handling
class SettingsWindow: NSWindow {
    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 { // ESC key code
            close()
        } else {
            super.keyDown(with: event)
        }
    }
}

class ModernSettingsWindowController: NSWindowController {
    static let shared = ModernSettingsWindowController()
    
    private init() {
        let window = SettingsWindow(
            contentRect: NSRect(x: 0, y: 0, width: 900, height: 600),
            styleMask: [.titled, .closable, .resizable],
            backing: .buffered,
            defer: false
        )
        
        super.init(window: window)
        
        window.title = "Potter Settings"
        window.center()
        window.isReleasedWhenClosed = false
        window.minSize = NSSize(width: 800, height: 500)
        
        // Create SwiftUI view that matches the Python design
        if #available(macOS 14.0, *) {
            let settingsView = ModernSettingsView()
            let hostingView = NSHostingView(rootView: settingsView)
            window.contentView = hostingView
        } else {
            // Fallback for older versions if needed
            fatalError("macOS 14.0+ required")
        }
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    override func showWindow(_ sender: Any?) {
        super.showWindow(sender)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

@available(macOS 14.0, *)
struct ModernSettingsView: View {
    @State private var selectedSection = 0
    @StateObject private var settings = PotterSettings()
    @StateObject private var logger = PotterLogger.shared
    @State private var logFilter: PotterLogger.LogEntry.LogLevel? = nil
    @Environment(\.colorScheme) var colorScheme
    
    // Prompts management
    @State private var prompts: [PromptItem] = []
    @State private var selectedPromptIndex: Int? = nil
    @State private var showingPromptDialog = false
    @State private var showingDeleteConfirmation = false
    @State private var isEditingPrompt = false
    
    let sections = [
        ("General", "gear"),
        ("Prompts", "text.bubble"),
        ("Advanced", "slider.horizontal.3"),
        ("Logs", "doc.text")
    ]
    
    var body: some View {
        HSplitView {
            // Sidebar
            sidebar
                .frame(minWidth: 200, maxWidth: 250)
            
            // Main content
            mainContent
                .frame(minWidth: 600)
        }
        .background(colorScheme == .dark ? Color(NSColor.windowBackgroundColor) : Color(NSColor.windowBackgroundColor))
        .onAppear {
            loadInitialPrompts()
        }
    }
    
    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            Text("Settings")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
                .padding(.horizontal, 20)
                .padding(.top, 20)
                .padding(.bottom, 10)
            
            Divider()
                .padding(.horizontal, 20)
                .padding(.bottom, 10)
            
            // Section buttons
            VStack(alignment: .leading, spacing: 4) {
                ForEach(Array(sections.enumerated()), id: \.offset) { index, section in
                    Button(action: {
                        selectedSection = index
                    }) {
                        HStack {
                            Image(systemName: section.1)
                                .foregroundColor(selectedSection == index ? .white : .secondary)
                                .frame(width: 18)
                                .font(.system(size: 16))
                            Text(section.0)
                                .foregroundColor(selectedSection == index ? .white : .primary)
                                .font(.system(size: 15, weight: .medium))
                            Spacer()
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 12)
                        .background(
                            selectedSection == index ?
                            Color.accentColor :
                            Color.clear
                        )
                        .cornerRadius(6)
                        .contentShape(Rectangle())
                    }
                    .buttonStyle(PlainButtonStyle())
                    .padding(.horizontal, 8)
                }
            }
            .padding(.top, 5)
            
            Spacer()
            
            // Footer
            VStack(alignment: .leading, spacing: 8) {
                Divider()
                    .padding(.horizontal, 20)
                
                HStack {
                    Button("Cancel") {
                        ModernSettingsWindowController.shared.close()
                    }
                    .buttonStyle(.bordered)
                    
                    Spacer()
                    
                    Button("Quit") {
                        NSApplication.shared.terminate(nil)
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 20)
            }
        }
        .background(colorScheme == .dark ? Color(NSColor.controlBackgroundColor) : Color(NSColor.controlBackgroundColor))
    }
    
    private var mainContent: some View {
        VStack(alignment: .leading, spacing: 0) {
            switch selectedSection {
            case 0:
                generalSection // Now has its own padding and scrolling
            case 1:
                promptsSection
            case 2:
                advancedSection
            case 3:
                logsSection
            default:
                generalSection
            }
        }
        .padding(selectedSection == 0 ? 0 : 20) // No padding for General tab (it handles its own)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
    
    private var generalSection: some View {
        ScrollView(.vertical, showsIndicators: true) {
            VStack(alignment: .leading, spacing: 20) {
                Text("General")
                    .font(.title)
                    .fontWeight(.semibold)
                
                // Use the new LLM Provider View
                LLMProviderView()
                    .padding(.bottom, 10)
                
                // Permissions Section
                GroupBox("Permissions") {
                    PermissionsView()
                        .padding(.vertical, 8)
                }
                .padding(.bottom, 10)
                
                
                // Extra padding at bottom for scrolling
                Color.clear
                    .frame(height: 50)
            }
            .padding(.horizontal, 20)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    // Permissions are now integrated into the General tab
    
    private var promptsSection: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Prompts")
                .font(.title)
                .fontWeight(.semibold)
            
            Text("Customize the AI prompts used for text processing")
                .foregroundColor(.secondary)
            
            Text("Double-click to edit. Use + and - buttons to add/remove.")
                .foregroundColor(.secondary)
                .font(.caption)
            
            // Prompts table (simplified version)
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("Name")
                        .fontWeight(.medium)
                        .frame(width: 120, alignment: .leading)
                    Text("Prompt Text")
                        .fontWeight(.medium)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                .padding()
                .background(Color(NSColor.controlBackgroundColor))
                
                Divider()
                
                // Rows
                ForEach(Array(prompts.enumerated()), id: \.element.id) { index, promptItem in
                    HStack {
                        Text(promptItem.name)
                            .frame(width: 120, alignment: .leading)
                        Text(promptItem.prompt)
                            .lineLimit(2)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .foregroundColor(.secondary)
                    }
                    .padding()
                    .background(
                        selectedPromptIndex == index ? 
                        Color.accentColor.opacity(0.1) : 
                        Color(NSColor.textBackgroundColor)
                    )
                    .simultaneousGesture(
                        TapGesture(count: 2)
                            .onEnded {
                                selectedPromptIndex = index
                                editPrompt(at: index)
                            }
                    )
                    .simultaneousGesture(
                        TapGesture(count: 1)
                            .onEnded {
                                selectedPromptIndex = index
                            }
                    )
                    
                    if index < prompts.count - 1 {
                        Divider()
                    }
                }
            }
            .overlay(
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color(NSColor.separatorColor))
            )
            
            HStack {
                Button("+") {
                    addNewPrompt()
                }
                .buttonStyle(.bordered)
                
                Button("-") {
                    deleteSelectedPrompt()
                }
                .buttonStyle(.bordered)
                .disabled(selectedPromptIndex == nil)
                
                Spacer()
                
                Text("\(prompts.count) prompts")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
            
            Spacer()
        }
        .sheet(isPresented: $showingPromptDialog) {
            if #available(macOS 14.0, *) {
                PromptEditDialog(
                    isPresented: $showingPromptDialog,
                    isEditing: isEditingPrompt,
                    existingPrompt: selectedPromptIndex != nil ? prompts[selectedPromptIndex!] : nil,
                    existingPromptNames: prompts.map { $0.name },
                    onSave: { name, prompt in
                        savePrompt(name: name, prompt: prompt)
                    }
                )
            } else {
                // Fallback for older macOS versions
                VStack {
                    Text("Prompt editing requires macOS 14.0 or later")
                        .padding()
                    Button("OK") {
                        showingPromptDialog = false
                    }
                    .buttonStyle(.borderedProminent)
                }
                .frame(width: 300, height: 100)
            }
        }
        .alert("Delete Prompt", isPresented: $showingDeleteConfirmation) {
            Button("Delete", role: .destructive) {
                confirmDeletePrompt()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            if let index = selectedPromptIndex, index < prompts.count {
                Text("Are you sure you want to delete the prompt '\(prompts[index].name)'? This action cannot be undone.")
            }
        }
    }
    
    private var advancedSection: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Advanced Settings")
                .font(.title)
                .fontWeight(.semibold)
            
            GroupBox("Build Information") {
                VStack(alignment: .leading, spacing: 10) {
                    infoRow("Build ID:", "swift_dev_build")
                    infoRow("Version:", "development")
                    infoRow("Built:", DateFormatter.localizedString(from: Date(), dateStyle: .medium, timeStyle: .short))
                }
                .padding()
            }
            
            GroupBox("Environment Information") {
                VStack(alignment: .leading, spacing: 10) {
                    infoRow("Mode:", "Development")
                    infoRow("Swift:", "5.9")
                    infoRow("macOS:", ProcessInfo.processInfo.operatingSystemVersionString)
                }
                .padding()
            }
            
            Spacer()
        }
    }
    
    private var logsSection: some View {
        VStack(alignment: .leading, spacing: 20) {
            logsSectionHeader
            logsSectionControls
            logsSectionContent
            logsSectionFooter
            Spacer()
        }
    }
    
    private var logsSectionHeader: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Application Logs")
                .font(.title)
                .fontWeight(.semibold)
            
            Text("View application logs for debugging and troubleshooting")
                .foregroundColor(.secondary)
        }
    }
    
    private var logsSectionControls: some View {
        HStack {
            Text("Filter:")
            Picker("Filter", selection: $logFilter) {
                Text("All").tag(nil as PotterLogger.LogEntry.LogLevel?)
                Text("Info").tag(PotterLogger.LogEntry.LogLevel.info as PotterLogger.LogEntry.LogLevel?)
                Text("Warning").tag(PotterLogger.LogEntry.LogLevel.warning as PotterLogger.LogEntry.LogLevel?)
                Text("Error").tag(PotterLogger.LogEntry.LogLevel.error as PotterLogger.LogEntry.LogLevel?)
                Text("Debug").tag(PotterLogger.LogEntry.LogLevel.debug as PotterLogger.LogEntry.LogLevel?)
            }
            .pickerStyle(MenuPickerStyle())
            .frame(width: 100)
            
            Spacer()
            
            Button("Refresh") {
                // Logs auto-refresh via @StateObject
            }
            
            Button("Clear") {
                logger.clearLogs()
            }
            
            Button("Open File") {
                if let fileURL = logger.saveLogsToFile() {
                    NSWorkspace.shared.open(fileURL)
                }
            }
        }
    }
    
    private var logsSectionContent: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 2) {
                let filteredLogs = logger.filteredEntries(level: logFilter)
                ForEach(Array(filteredLogs.enumerated()), id: \.offset) { _, logEntry in
                    logEntryRow(logEntry)
                }
            }
            .padding(.vertical, 8)
        }
        .frame(height: 300)
        .background(Color(NSColor.textBackgroundColor))
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color(NSColor.separatorColor))
        )
    }
    
    private func logEntryRow(_ logEntry: PotterLogger.LogEntry) -> some View {
        HStack(alignment: .top, spacing: 8) {
            Circle()
                .fill(Color(logEntry.level.color))
                .frame(width: 6, height: 6)
                .padding(.top, 6)
            
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(DateFormatter.timeFormatter.string(from: logEntry.timestamp))
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundColor(.secondary)
                    
                    Text(logEntry.component)
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundColor(Color(logEntry.level.color))
                        .fontWeight(.medium)
                    
                    Text(logEntry.level.rawValue)
                        .font(.system(.caption2, design: .monospaced))
                        .foregroundColor(Color(logEntry.level.color))
                        .fontWeight(.bold)
                }
                
                Text(logEntry.message)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundColor(.primary)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 4)
        .background(Color(NSColor.controlBackgroundColor).opacity(0.3))
    }
    
    private var logsSectionFooter: some View {
        let totalLogs = logger.logEntries.count
        let filteredCount = logger.filteredEntries(level: logFilter).count
        return Text("Showing \(filteredCount) of \(totalLogs) log entries")
            .foregroundColor(.secondary)
            .font(.caption)
    }
    
    private func infoRow(_ label: String, _ value: String) -> some View {
        HStack {
            Text(label)
                .frame(width: 80, alignment: .leading)
            Text(value)
                .foregroundColor(.secondary)
            Spacer()
        }
    }
    
    // MARK: - Prompts Management Functions
    private func loadInitialPrompts() {
        prompts = PromptManager.shared.loadPrompts()
    }
    
    private func addNewPrompt() {
        isEditingPrompt = false
        selectedPromptIndex = nil
        showingPromptDialog = true
    }
    
    private func editPrompt(at index: Int) {
        guard index < prompts.count else { return }
        isEditingPrompt = true
        selectedPromptIndex = index
        showingPromptDialog = true
    }
    
    private func deleteSelectedPrompt() {
        guard selectedPromptIndex != nil else { return }
        showingDeleteConfirmation = true
    }
    
    private func confirmDeletePrompt() {
        guard let index = selectedPromptIndex, index < prompts.count else { return }
        prompts.remove(at: index)
        selectedPromptIndex = nil
        PromptManager.shared.savePrompts(prompts)
        PotterLogger.shared.info("settings", "🗑️ Deleted prompt at index \(index)")
    }
    
    private func savePrompt(name: String, prompt: String) {
        if isEditingPrompt, let index = selectedPromptIndex {
            // Update existing prompt
            prompts[index].name = name
            prompts[index].prompt = prompt
            PotterLogger.shared.info("settings", "✏️ Updated prompt: \(name)")
        } else {
            // Add new prompt
            let newPrompt = PromptItem(name: name, prompt: prompt)
            prompts.append(newPrompt)
            PotterLogger.shared.info("settings", "➕ Added new prompt: \(name)")
        }
        PromptManager.shared.savePrompts(prompts)
        selectedPromptIndex = nil
    }
    
    
    // API key management is now handled by LLMProviderView
}

// MARK: - Hotkey Configuration View
@available(macOS 14.0, *)
struct HotkeyConfigurationView: View {
    @State private var isCapturingHotkey = false
    @State private var capturedKeys: [String] = []
    @State private var currentHotkey = ["⌘", "⇧", "R"]
    @State private var previousHotkey = ["⌘", "⇧", "R"] // Store previous combo for ESC
    @State private var warningMessage = ""
    @FocusState private var isKeyCaptureFocused: Bool
    @StateObject private var permissionManager = PermissionManager.shared
    
    private var isAccessibilityGranted: Bool {
        permissionManager.accessibilityStatus == .granted
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Global Hotkey:")
                    .fontWeight(.medium)
                
                // Hotkey Pills
                HStack(spacing: 6) {
                    if isCapturingHotkey {
                        // Show captured keys in real-time
                        ForEach(capturedKeys.indices, id: \.self) { index in
                            hotkeyPill(capturedKeys[index], isActive: true)
                        }
                        
                        // Show placeholder for remaining keys
                        if capturedKeys.count < 3 {
                            ForEach(capturedKeys.count..<3, id: \.self) { _ in
                                hotkeyPill("?", isActive: false)
                            }
                        }
                    } else {
                        // Show current hotkey
                        ForEach(currentHotkey.indices, id: \.self) { index in
                            hotkeyPill(currentHotkey[index], isActive: false, isDisabled: !isAccessibilityGranted)
                                .onTapGesture {
                                    if isAccessibilityGranted {
                                        startHotkeyCapture()
                                    }
                                }
                        }
                    }
                }
                
                Spacer()
                
                // Reset Button
                Button("Reset") {
                    resetToDefault()
                }
                .buttonStyle(.bordered)
                .disabled(isCapturingHotkey || !isAccessibilityGranted)
            }
            
            // Accessibility warning when permissions not granted
            if !isAccessibilityGranted {
                Text("Accessibility permission required to use global hotkeys")
                    .foregroundColor(.orange)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            
            // Warning message
            if !warningMessage.isEmpty {
                Text(warningMessage)
                    .foregroundColor(.orange)
                    .font(.caption)
                    .fontWeight(.medium)
            }
            
            // Instructions when capturing
            if isCapturingHotkey {
                Text("Press your desired key combination (3 keys minimum) or ESC to cancel")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
        }
        .background(
            // Invisible text field to capture key events
            TextField("", text: .constant(""))
                .opacity(0)
                .focused($isKeyCaptureFocused)
                .onKeyPress { keyPress in
                    if isCapturingHotkey {
                        return handleKeyPress(keyPress)
                    }
                    return .ignored
                }
        )
    }
    
    private func hotkeyPill(_ text: String, isActive: Bool, isDisabled: Bool = false) -> some View {
        Text(text)
            .font(.system(.body, design: .monospaced))
            .fontWeight(.medium)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(
                        isActive ? Color.accentColor :
                        isDisabled ? Color.secondary.opacity(0.1) :
                        Color.secondary.opacity(0.2)
                    )
            )
            .foregroundColor(
                isActive ? .white :
                isDisabled ? .secondary :
                .primary
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(
                        isActive ? Color.accentColor :
                        isDisabled ? Color.secondary.opacity(0.2) :
                        Color.secondary.opacity(0.4),
                        lineWidth: 1
                    )
            )
    }
    
    private func startHotkeyCapture() {
        previousHotkey = currentHotkey // Store current combo before changing
        isCapturingHotkey = true
        capturedKeys.removeAll()
        warningMessage = ""
        isKeyCaptureFocused = true
        
        PotterLogger.shared.info("settings", "🎹 Started hotkey capture mode")
    }
    
    private func handleKeyPress(_ keyPress: KeyPress) -> KeyPress.Result {
        let key = keyPress.key
        
        // Handle ESC to cancel
        if key == .escape {
            cancelHotkeyCapture()
            return .handled
        }
        
        // Clear previous capture to build new combination
        capturedKeys.removeAll()
        
        // Handle modifiers first (add each separately)
        if keyPress.modifiers.contains(.command) {
            capturedKeys.append("⌘")
        }
        if keyPress.modifiers.contains(.shift) {
            capturedKeys.append("⇧")
        }
        if keyPress.modifiers.contains(.option) {
            capturedKeys.append("⌥")
        }
        if keyPress.modifiers.contains(.control) {
            capturedKeys.append("⌃")
        }
        
        // Handle regular keys (add as separate key)
        var regularKey = ""
        switch key {
        case KeyEquivalent.space:
            regularKey = "Space"
        case KeyEquivalent.tab:
            regularKey = "Tab"
        case KeyEquivalent.return:
            regularKey = "Return"  
        case KeyEquivalent.delete:
            regularKey = "Delete"
        case KeyEquivalent.upArrow:
            regularKey = "↑"
        case KeyEquivalent.downArrow:
            regularKey = "↓"
        case KeyEquivalent.leftArrow:
            regularKey = "←"
        case KeyEquivalent.rightArrow:
            regularKey = "→"
        default:
            // For character keys, convert to string
            let char = key.character
            regularKey = String(char).uppercased()
        }
        
        // Add regular key if it's not empty and not just a modifier
        if !regularKey.isEmpty && !["⌘", "⇧", "⌥", "⌃"].contains(regularKey) {
            capturedKeys.append(regularKey)
        }
        
        // Validate key combination
        validateKeyCombo()
        
        return .handled
    }
    
    private func validateKeyCombo() {
        if capturedKeys.count < 3 {
            warningMessage = "3 keys needed for hotkey combination"
        } else {
            // Check for conflicts
            let conflictMessage = checkForShortcutConflicts(capturedKeys)
            if !conflictMessage.isEmpty {
                warningMessage = conflictMessage
            } else {
                warningMessage = ""
                // Auto-apply after a brief moment
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
                    if isCapturingHotkey && capturedKeys.count >= 3 {
                        applyNewHotkey()
                    }
                }
            }
        }
    }
    
    private func checkForShortcutConflicts(_ keys: [String]) -> String {
        let combo = keys.joined(separator: "+")
        
        // Common macOS system shortcuts
        let systemShortcuts: [String: String] = [
            "⌘+Q": "Quit Application",
            "⌘+W": "Close Window",
            "⌘+N": "New Window",
            "⌘+T": "New Tab",
            "⌘+S": "Save",
            "⌘+O": "Open",
            "⌘+P": "Print",
            "⌘+Z": "Undo",
            "⌘+⇧+Z": "Redo",
            "⌘+C": "Copy",
            "⌘+V": "Paste",
            "⌘+X": "Cut",
            "⌘+A": "Select All",
            "⌘+F": "Find",
            "⌘+G": "Find Next",
            "⌘+H": "Hide Application",
            "⌘+M": "Minimize Window",
            "⌘+R": "Refresh/Reload",
            "⌘+,": "Preferences",
            "⌘+Space": "Spotlight Search",
            "⌘+Tab": "Application Switcher",
            "⌘+⇧+3": "Screenshot",
            "⌘+⇧+4": "Screenshot Selection",
            "⌘+⇧+5": "Screenshot Options",
            "⌘+⌃+Space": "Emoji Picker",
            "⌘+⇧+A": "Applications Folder",
            "⌘+⇧+U": "Utilities Folder",
            "⌘+⇧+H": "Home Folder",
            "⌘+⇧+D": "Desktop Folder",
            "⌘+⇧+O": "Documents Folder",
            "⌘+⇧+G": "Go to Folder",
            "⌘+⇧+Delete": "Empty Trash",
            "⌘+⌥+ESC": "Force Quit Applications"
        ]
        
        if let conflictName = systemShortcuts[combo] {
            return "⚠️ Conflicts with system shortcut: \(conflictName)"
        }
        
        // Check for potential app conflicts (common shortcuts)
        let commonAppShortcuts: [String: String] = [
            "⌘+⇧+I": "Inspector/DevTools",
            "⌘+⇧+C": "Color Picker",
            "⌘+⇧+L": "Location/Library",
            "⌘+⇧+K": "Clear/Clean",
            "⌘+⇧+E": "Export",
            "⌘+⇧+P": "Private/Incognito",
            "⌘+⌥+I": "Developer Tools"
        ]
        
        if let conflictName = commonAppShortcuts[combo] {
            return "⚠️ May conflict with app shortcut: \(conflictName)"
        }
        
        return ""
    }
    
    private func applyNewHotkey() {
        currentHotkey = Array(capturedKeys.prefix(3))
        isCapturingHotkey = false
        isKeyCaptureFocused = false
        warningMessage = ""
        
        PotterLogger.shared.info("settings", "🎹 Applied new hotkey: \(currentHotkey.joined(separator: "+"))")
        
        // TODO: Save to settings and update global hotkey system
    }
    
    private func cancelHotkeyCapture() {
        currentHotkey = previousHotkey // Restore previous combo on ESC
        isCapturingHotkey = false
        isKeyCaptureFocused = false
        capturedKeys.removeAll()
        warningMessage = ""
        
        PotterLogger.shared.info("settings", "🎹 Cancelled hotkey capture - restored previous combo")
    }
    
    private func resetToDefault() {
        currentHotkey = ["⌘", "⇧", "R"]
        previousHotkey = ["⌘", "⇧", "R"]
        warningMessage = ""
        capturedKeys.removeAll()
        isCapturingHotkey = false
        isKeyCaptureFocused = false
        
        PotterLogger.shared.info("settings", "🎹 Reset hotkey to default")
        
        // TODO: Save to settings and update global hotkey system
    }
}

// MARK: - Prompt Edit Dialog
@available(macOS 14.0, *)
struct PromptEditDialog: View {
    @Binding var isPresented: Bool
    let isEditing: Bool
    let existingPrompt: PromptItem?
    let existingPromptNames: [String]
    let onSave: (String, String) -> Void
    
    @State private var name: String = ""
    @State private var prompt: String = ""
    @State private var errorMessage: String = ""
    @FocusState private var isNameFocused: Bool
    @Environment(\.colorScheme) var colorScheme
    
    var body: some View {
        VStack(spacing: 0) {
            // Header with app icon
            HStack(spacing: 16) {
                Image(systemName: "wand.and.stars")
                    .font(.system(size: 32))
                    .foregroundColor(.blue)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(isEditing ? "Edit Prompt" : "New Prompt")
                        .font(.title2)
                        .fontWeight(.semibold)
                    
                    Text(isEditing ? "Modify the existing prompt" : "Create a new prompt for text processing")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.top, 24)
            .padding(.bottom, 16)
            
            Divider()
            
            // Form content
            VStack(alignment: .leading, spacing: 20) {
                // Name field
                VStack(alignment: .leading, spacing: 8) {
                    Text("Name")
                        .font(.headline)
                        .fontWeight(.medium)
                    
                    TextField("Enter prompt name", text: $name)
                        .textFieldStyle(.roundedBorder)
                        .focused($isNameFocused)
                        .onSubmit {
                            // Move focus to prompt field when name is submitted
                        }
                    
                    Text("Must be unique and descriptive")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                // Prompt field
                VStack(alignment: .leading, spacing: 8) {
                    Text("Prompt Text")
                        .font(.headline)
                        .fontWeight(.medium)
                    
                    VStack(alignment: .trailing, spacing: 4) {
                        if #available(macOS 14.0, *) {
                            TextEditor(text: $prompt)
                                .frame(minHeight: 150, maxHeight: 250)
                                .padding(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 6)
                                        .stroke(Color(NSColor.separatorColor), lineWidth: 1)
                                )
                                .onKeyPress { keyPress in
                                    if keyPress.key == .escape {
                                        cancelDialog()
                                        return .handled
                                    }
                                    return .ignored
                                }
                        } else {
                            TextField("Enter prompt text", text: $prompt, axis: .vertical)
                                .textFieldStyle(.roundedBorder)
                                .frame(minHeight: 120)
                        }
                        
                        Text("\(prompt.count)/500 characters")
                            .font(.caption)
                            .foregroundColor(prompt.count > 500 ? .red : .secondary)
                    }
                    
                    Text("Describe what you want the AI to do with the selected text")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                // Error message
                if !errorMessage.isEmpty {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .font(.caption)
                        .fontWeight(.medium)
                }
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 20)
            
            Divider()
            
            // Footer buttons
            HStack {
                Button("Cancel") {
                    cancelDialog()
                }
                .buttonStyle(.bordered)
                .keyboardShortcut(.escape, modifiers: [])
                
                Spacer()
                
                Button(isEditing ? "Update" : "Create") {
                    savePrompt()
                }
                .buttonStyle(.borderedProminent)
                .keyboardShortcut(.return, modifiers: .command)
                .disabled(!isValidInput())
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
        }
        .frame(width: 600, height: 500)
        .background(Color(NSColor.windowBackgroundColor))
        .onAppear {
            loadExistingData()
            isNameFocused = true
        }
    }
    
    private func loadExistingData() {
        if let existing = existingPrompt {
            name = existing.name
            prompt = existing.prompt
        }
    }
    
    private func isValidInput() -> Bool {
        !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        prompt.count <= 500 &&
        (isEditing || !existingPromptNames.contains(name.trimmingCharacters(in: .whitespacesAndNewlines))) &&
        (!isEditing || existingPrompt?.name == name || !existingPromptNames.contains(name.trimmingCharacters(in: .whitespacesAndNewlines)))
    }
    
    private func savePrompt() {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedPrompt = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Validate name uniqueness
        if !isEditing && existingPromptNames.contains(trimmedName) {
            errorMessage = "A prompt with this name already exists"
            return
        }
        
        if isEditing && existingPrompt?.name != trimmedName && existingPromptNames.contains(trimmedName) {
            errorMessage = "A prompt with this name already exists"
            return
        }
        
        // Validate prompt length
        if trimmedPrompt.count > 500 {
            errorMessage = "Prompt text must be 500 characters or less"
            return
        }
        
        // Validate required fields
        if trimmedName.isEmpty {
            errorMessage = "Name is required"
            return
        }
        
        if trimmedPrompt.isEmpty {
            errorMessage = "Prompt text is required"
            return
        }
        
        onSave(trimmedName, trimmedPrompt)
        isPresented = false
    }
    
    private func cancelDialog() {
        isPresented = false
    }
}