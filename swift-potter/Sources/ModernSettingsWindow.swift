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
    
    // For testing - allows override of file path
    private var testFileURL: URL?
    
    private var promptsFileURL: URL {
        // Use test file URL if set (for testing)
        if let testURL = testFileURL {
            return testURL
        }
        
        // Always use Application Support to ensure consistency between command line and app bundle
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let potterDir = appSupport.appendingPathComponent("Potter")
        
        // Create directory if it doesn't exist
        try? FileManager.default.createDirectory(at: potterDir, withIntermediateDirectories: true)
        
        return potterDir.appendingPathComponent("prompts.json")
    }
    
    // For testing - allows setting a custom file path
    func setTestFileURL(_ url: URL?) {
        testFileURL = url
        if let url = url {
            // Create parent directory if needed
            try? FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
        }
    }
    
    func loadPrompts() -> [PromptItem] {
        // Check if file exists, if not create it with defaults
        if !FileManager.default.fileExists(atPath: promptsFileURL.path) {
            let defaults = defaultPrompts()
            savePrompts(defaults)
            PotterLogger.shared.debug("prompts", "📄 Created new prompts file with \(defaults.count) default prompts at \(promptsFileURL.path)")
            return defaults
        }
        
        // File exists, load from it
        do {
            let data = try Data(contentsOf: promptsFileURL)
            let prompts = try JSONDecoder().decode([PromptItem].self, from: data)
            PotterLogger.shared.debug("prompts", "📖 Loaded \(prompts.count) prompts from \(promptsFileURL.path)")
            return prompts
        } catch {
            PotterLogger.shared.error("prompts", "📖 Failed to load prompts file: \(error.localizedDescription)")
            // If file is corrupted, try to preserve any readable content and only add defaults if totally empty
            PotterLogger.shared.warning("prompts", "📄 Corrupted prompts file detected - preserving any existing data")
            
            // Try to read as raw text to see if there's any content
            if let rawData = try? String(contentsOf: promptsFileURL),
               !rawData.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                PotterLogger.shared.warning("prompts", "📄 Non-empty corrupted file detected - returning defaults without overwriting")
                // Return defaults but don't overwrite the file
                return defaultPrompts()
            } else {
                // File is actually empty or unreadable, safe to recreate
                let defaults = defaultPrompts()
                savePrompts(defaults)
                PotterLogger.shared.warning("prompts", "📄 Empty/unreadable prompts file recreated with defaults")
                return defaults
            }
        }
    }
    
    func savePrompts(_ prompts: [PromptItem]) {
        do {
            let data = try JSONEncoder().encode(prompts)
            try data.write(to: promptsFileURL)
            PotterLogger.shared.debug("prompts", "💾 Saved \(prompts.count) prompts to \(promptsFileURL.path)")
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
    @StateObject private var loginItemsManager = LoginItemsManager.shared
    @State private var logFilter: PotterLogger.LogEntry.LogLevel? = nil
    @Environment(\.colorScheme) var colorScheme
    
    // Prompts management
    @State private var prompts: [PromptItem] = []
    @State private var selectedPromptIndex: Int? = nil
    @State private var showingDeleteConfirmation = false
    @State private var currentPromptDialog: PromptEditDialogController? = nil  // Keep strong reference
    
    let sections = [
        ("General", "gear"),
        ("Prompts", "bubble.left.and.bubble.right"),
        ("About", "info.circle"),
        ("Logs", "list.bullet.rectangle")
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
                
                // Start at Login Section
                GroupBox("Startup") {
                    startAtLoginView
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
    
    private var startAtLoginView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Toggle("Start Potter at login", isOn: Binding(
                    get: { loginItemsManager.isEnabled },
                    set: { newValue in
                        if newValue {
                            loginItemsManager.enable()
                        } else {
                            loginItemsManager.disable()
                        }
                    }
                ))
                Spacer()
            }
            
            Text("Potter will automatically start when you log in to your Mac.")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.leading, 20) // Align with checkbox text
        }
        .onAppear {
            loginItemsManager.checkCurrentStatus()
        }
    }
    
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
        // Note: Prompt dialog is now handled by AppKit modal in addNewPrompt() and editPrompt() functions
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
            Text("About")
                .font(.title)
                .fontWeight(.semibold)
            
            GroupBox("Build Information") {
                VStack(alignment: .leading, spacing: 12) {
                    let buildInfo = BuildInfo.current()
                    
                    // Featured build name with emphasis
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Build Name")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text(buildInfo.buildName)
                            .font(.title3)
                            .fontWeight(.semibold)
                            .foregroundColor(.primary)
                    }
                    
                    Divider()
                        .padding(.vertical, 4)
                    
                    infoRow("Build ID:", buildInfo.buildId)
                    infoRow("Version:", "\(buildInfo.version) • \(buildInfo.versionCodename)")
                    infoRow("Built:", buildInfo.buildDate)
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
            
            // About Section
            GroupBox("About") {
                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 4) {
                        Text("Developed by")
                            .foregroundColor(.secondary)
                        
                        Button("graydot") {
                            if let url = URL(string: "https://graydot.ai") {
                                NSWorkspace.shared.open(url)
                            }
                        }
                        .buttonStyle(.plain)
                        .foregroundColor(.blue)
                        .underline()
                        
                        Text("with")
                            .foregroundColor(.secondary)
                        
                        Text("♥")
                            .foregroundColor(.red)
                    }
                    
                    HStack {
                        Text("Product link for Potter:")
                            .foregroundColor(.secondary)
                        
                        Button(action: {
                            if let url = URL(string: "https://graydot.ai/products/potter/") {
                                NSWorkspace.shared.open(url)
                            }
                        }) {
                            HStack(spacing: 4) {
                                if let appIcon = NSImage(named: "AppIcon") {
                                    Image(nsImage: appIcon)
                                        .resizable()
                                        .frame(width: 16, height: 16)
                                } else {
                                    Image(systemName: "wand.and.stars")
                                        .frame(width: 16, height: 16)
                                }
                                Text("potter")
                            }
                        }
                        .buttonStyle(.plain)
                        .foregroundColor(.blue)
                        .underline()
                    }
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
            Picker("", selection: $logFilter) {
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
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 2) {
                    let filteredLogs = logger.filteredEntries(level: logFilter)
                    ForEach(Array(filteredLogs.enumerated()), id: \.offset) { index, logEntry in
                        selectableLogEntryRow(logEntry)
                            .id(index) // Add ID for scrolling
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
            .onChange(of: logger.logEntries.count) { _ in
                // Auto-scroll to bottom when new logs are added
                let filteredLogs = logger.filteredEntries(level: logFilter)
                if !filteredLogs.isEmpty {
                    withAnimation(.easeOut(duration: 0.3)) {
                        proxy.scrollTo(filteredLogs.count - 1, anchor: .bottom)
                    }
                }
            }
        }
    }
    
    private func selectableLogEntryRow(_ logEntry: PotterLogger.LogEntry) -> some View {
        let timestamp = DateFormatter.timeFormatter.string(from: logEntry.timestamp)
        let logText = "\(timestamp) - \(logEntry.component) - \(logEntry.level.rawValue) - \(logEntry.message)"
        
        return HStack(alignment: .top, spacing: 8) {
            Circle()
                .fill(Color(logEntry.level.color))
                .frame(width: 6, height: 6)
                .padding(.top, 6)
            
            Text(logText)
                .font(.system(.caption, design: .monospaced))
                .foregroundColor(.primary)
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
                .multilineTextAlignment(.leading)
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
        selectedPromptIndex = nil  // Clear index for new prompt
        currentPromptDialog = PromptEditDialogController(
            isEditing: false,
            existingPrompt: nil,
            existingPromptNames: prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt in
            self.savePrompt(name: name, prompt: prompt)
            self.currentPromptDialog = nil  // Release after save
        }
        currentPromptDialog?.showModal()
    }
    
    private func editPrompt(at index: Int) {
        guard index < prompts.count else { return }
        selectedPromptIndex = index  // Set the index for editing
        currentPromptDialog = PromptEditDialogController(
            isEditing: true,
            existingPrompt: prompts[index],
            existingPromptNames: prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt in
            self.savePrompt(name: name, prompt: prompt)
            self.currentPromptDialog = nil  // Release after save
        }
        currentPromptDialog?.showModal()
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
        if let index = selectedPromptIndex {
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
    @State private var currentHotkey = ["⌘", "⇧", "9"]
    @State private var previousHotkey = ["⌘", "⇧", "9"] // Store previous combo for ESC
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
                .disabled(isCapturingHotkey)
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
    
    private func getBaseCharacter(from character: Character) -> String {
        // Map shifted characters to their base characters
        let shiftedCharacterMap: [Character: String] = [
            "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
            "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
            "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\",
            ":": ";", "\"": "'", "<": ",", ">": ".", "?": "/",
            "~": "`"
        ]
        
        // If it's a shifted character, return the base character
        if let baseChar = shiftedCharacterMap[character] {
            return baseChar
        }
        
        // Otherwise return the character as uppercase
        return String(character).uppercased()
    }
    
    private func startHotkeyCapture() {
        previousHotkey = currentHotkey // Store current combo before changing
        isCapturingHotkey = true
        capturedKeys.removeAll()
        warningMessage = ""
        isKeyCaptureFocused = true
        
        // Disable global hotkey during capture to prevent interference
        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore.disableGlobalHotkey()
        }
        
        PotterLogger.shared.debug("settings", "🎹 Started hotkey capture mode")
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
            // For character keys, get the base character (handles shifted characters)
            let char = key.character
            regularKey = getBaseCharacter(from: char)
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
        
        // Update the global hotkey system (this will re-enable it with new combo)
        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore.updateHotkey(currentHotkey)
        }
    }
    
    private func cancelHotkeyCapture() {
        currentHotkey = previousHotkey // Restore previous combo on ESC
        isCapturingHotkey = false
        isKeyCaptureFocused = false
        capturedKeys.removeAll()
        warningMessage = ""
        
        // Re-enable global hotkey with previous combo
        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore.enableGlobalHotkey()
        }
        
        PotterLogger.shared.debug("settings", "🎹 Cancelled hotkey capture - restored previous combo")
    }
    
    private func resetToDefault() {
        currentHotkey = ["⌘", "⇧", "9"]
        previousHotkey = ["⌘", "⇧", "9"]
        warningMessage = ""
        capturedKeys.removeAll()
        
        PotterLogger.shared.info("settings", "🎹 Reset hotkey to default")
        
        // Update the global hotkey system
        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore.updateHotkey(currentHotkey)
        }
        
        // Start capture mode like clicking on pills does
        startHotkeyCapture()
    }
}


