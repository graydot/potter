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


// MARK: - Custom Window for ESC Handling
class SettingsWindow: NSWindow {
    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 { // ESC key code
            close()
        } else {
            super.keyDown(with: event)
        }
    }
    
    override func close() {
        super.close()
        
        // Switch back to accessory app when window closes
        NSApp.setActivationPolicy(.accessory)
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
        // Switch to regular app so it appears in Alt+Tab
        NSApp.setActivationPolicy(.regular)
        
        super.showWindow(sender)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
    
    override func close() {
        super.close()
        
        // Switch back to accessory app (menu bar only)
        NSApp.setActivationPolicy(.accessory)
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
    @StateObject private var promptService = PromptService.shared
    @State private var selectedPromptIndex: Int? = nil
    @State private var showingDeleteConfirmation = false
    @State private var currentPromptDialog: PromptEditDialogController? = nil  // Keep strong reference
    
    
    let sections = [
        ("General", "gear"),
        ("Prompts", "bubble.left.and.bubble.right"),
        ("Updates", "arrow.down.circle"),
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
            // PromptService loads automatically via @StateObject
        }
    }
    
    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            Text("Settings")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundColor(.primary)
                .padding(.leading, 16)
                .padding(.trailing, 8)
                .padding(.top, 20)
                .padding(.bottom, 10)
            
            Divider()
                .padding(.leading, 16)
                .padding(.trailing, 8)
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
                        .padding(.leading, 16)
                        .padding(.trailing, 8)
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
                    .padding(.horizontal, 4)
                }
            }
            .padding(.top, 5)
            
            Spacer()
            
            // Footer
            VStack(alignment: .leading, spacing: 8) {
                Divider()
                    .padding(.leading, 16)
                    .padding(.trailing, 8)
                
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
                .padding(.leading, 16)
                .padding(.trailing, 8)
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
                updatesSection
            case 3:
                advancedSection
            case 4:
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
                
                // Hotkey Configuration Section
                GroupBox("Global Hotkey") {
                    HotkeyView()
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
                ForEach(Array(promptService.prompts.enumerated()), id: \.element.id) { index, promptItem in
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
                    
                    if index < promptService.prompts.count - 1 {
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
                .disabled(selectedPromptIndex == nil || promptService.prompts.count <= 1)
                
                Spacer()
                
                Text("\(promptService.prompts.count) prompts")
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
            if let index = selectedPromptIndex, index < promptService.prompts.count {
                Text("Are you sure you want to delete the prompt '\(promptService.prompts[index].name)'? This action cannot be undone.")
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
            
            // Privacy Warning Section
            GroupBox {
                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                            .font(.title2)
                        
                        Text("Privacy Warning")
                            .font(.headline)
                            .fontWeight(.semibold)
                    }
                    
                    Text("This app processes your text using external AI services (OpenAI, Anthropic, Google). Potter and the app author do not store your text or keystrokes, but the AI providers will have access to any text you process. Avoid using this app with sensitive, confidential, or private information.")
                        .foregroundColor(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding()
            }
            
            // About Section
            HStack(alignment: .top, spacing: 20) {
                // Left side - About info
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
                        
                        HStack {
                            Text("Source code:")
                                .foregroundColor(.secondary)
                            
                            Button(action: {
                                if let url = URL(string: "https://github.com/graydot/potter") {
                                    NSWorkspace.shared.open(url)
                                }
                            }) {
                                HStack(spacing: 4) {
                                    Image(systemName: "chevron.left.forwardslash.chevron.right")
                                        .frame(width: 16, height: 16)
                                    Text("GitHub")
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
                
                // Right side - Data Management
                GroupBox("Data Management") {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Remove all Potter data and return to pristine state.")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                        
                        HStack {
                            Button(action: openPromptsFolder) {
                                HStack(spacing: 4) {
                                    Image(systemName: "folder")
                                        .frame(width: 14, height: 14)
                                    Text("Show prompts folder")
                                }
                            }
                            .buttonStyle(.plain)
                            .foregroundColor(.blue)
                            .underline()
                            .font(.caption)
                            
                            Spacer()
                        }
                        
                        Button("Delete All Data") {
                            showDeleteAllDataDialog()
                        }
                        .buttonStyle(.bordered)
                        .foregroundColor(.red)
                    }
                    .padding()
                }
                .frame(maxWidth: 200)
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
        VStack(spacing: 8) {
            // Copy All Logs button
            HStack {
                Button("Copy All Logs") {
                    let filteredLogs = logger.filteredEntries(level: logFilter)
                    let logText = filteredLogs.map { logEntry in
                        let timestamp = DateFormatter.timeFormatter.string(from: logEntry.timestamp)
                        return "\(timestamp) - \(logEntry.component) - \(logEntry.level.rawValue) - \(logEntry.message)"
                    }.joined(separator: "\n")
                    
                    let pasteboard = NSPasteboard.general
                    pasteboard.clearContents()
                    pasteboard.setString(logText, forType: .string)
                }
                .buttonStyle(.bordered)
                
                Spacer()
                
                Text("\(logger.filteredEntries(level: logFilter).count) entries")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }
            
            // Improved text view for better selection
            ScrollViewReader { proxy in
                TextEditor(text: .constant(formattedLogText()))
                    .font(.system(.caption, design: .monospaced))
                    .frame(height: 300)
                    .background(Color(NSColor.textBackgroundColor))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color(NSColor.separatorColor))
                    )
                    .onChange(of: logger.logEntries.count) { _ in
                        // Auto-scroll to bottom when new logs are added (but only if user hasn't manually scrolled)
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                            // Scroll to end of text
                            if let textView = findTextView() {
                                textView.scrollToEndOfDocument(nil)
                            }
                        }
                    }
            }
        }
    }
    
    private func formattedLogText() -> String {
        let filteredLogs = logger.filteredEntries(level: logFilter)
        return filteredLogs.map { logEntry in
            let timestamp = DateFormatter.timeFormatter.string(from: logEntry.timestamp)
            let levelIndicator = logEntry.level.emoji
            return "\(timestamp) \(levelIndicator) [\(logEntry.component)] \(logEntry.message)"
        }.joined(separator: "\n")
    }
    
    private func findTextView() -> NSTextView? {
        // Helper to find the underlying NSTextView for scrolling
        guard let window = NSApplication.shared.windows.first(where: { $0.title.contains("Potter") }) else { return nil }
        return findTextViewInView(window.contentView)
    }
    
    private func findTextViewInView(_ view: NSView?) -> NSTextView? {
        guard let view = view else { return nil }
        
        if let textView = view as? NSTextView {
            return textView
        }
        
        for subview in view.subviews {
            if let found = findTextViewInView(subview) {
                return found
            }
        }
        
        return nil
    }
    
    
    private var logsSectionFooter: some View {
        let totalLogs = logger.logEntries.count
        let filteredCount = logger.filteredEntries(level: logFilter).count
        return Text("Showing \(filteredCount) of \(totalLogs) log entries")
            .foregroundColor(.secondary)
            .font(.caption)
    }
    
    private var updatesSection: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Updates")
                .font(.title)
                .fontWeight(.semibold)
            
            // Current version info
            VStack(alignment: .leading, spacing: 12) {
                Text("Current Version")
                    .font(.headline)
                
                HStack {
                    Text("Version:")
                        .frame(width: 100, alignment: .leading)
                    Text(AutoUpdateManager.shared.getCurrentVersion())
                        .foregroundColor(.secondary)
                    Spacer()
                }
                
                HStack {
                    Text("Build:")
                        .frame(width: 100, alignment: .leading)
                    Text(AutoUpdateManager.shared.getBuildNumber())
                        .foregroundColor(.secondary)
                    Spacer()
                }
                
                if let lastCheck = AutoUpdateManager.shared.getLastUpdateCheckDate() {
                    HStack {
                        Text("Last Check:")
                            .frame(width: 100, alignment: .leading)
                        Text(DateFormatter.localizedString(from: lastCheck, dateStyle: .short, timeStyle: .short))
                            .foregroundColor(.secondary)
                        Spacer()
                    }
                }
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)
            
            // Auto-update settings
            VStack(alignment: .leading, spacing: 12) {
                Text("Update Settings")
                    .font(.headline)
                
                Toggle("Automatically check for updates", isOn: Binding(
                    get: { AutoUpdateManager.shared.getAutoUpdateEnabled() },
                    set: { enabled in
                        AutoUpdateManager.shared.setAutoUpdateEnabled(enabled)
                    }
                ))
                
                Text("Potter will check for updates daily and notify you when new versions are available.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
            .background(Color(NSColor.controlBackgroundColor))
            .cornerRadius(8)
            
            // Manual check button
            HStack {
                Button("Check for Updates Now") {
                    AutoUpdateManager.shared.checkForUpdatesManually()
                }
                .buttonStyle(.borderedProminent)
                
                Spacer()
                
                Button("Open Releases Page") {
                    if let url = URL(string: "https://github.com/graydot/potter/releases") {
                        NSWorkspace.shared.open(url)
                    }
                }
                .buttonStyle(.bordered)
            }
            
            Spacer()
        }
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
    private func addNewPrompt() {
        selectedPromptIndex = nil  // Clear index for new prompt
        currentPromptDialog = PromptEditDialogController(
            isEditing: false,
            existingPrompt: nil,
            existingPromptNames: promptService.prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt in
            self.handleSavePrompt(name: name, prompt: prompt)
            self.currentPromptDialog = nil  // Release after save
        }
        currentPromptDialog?.showModal()
    }
    
    private func editPrompt(at index: Int) {
        guard index < promptService.prompts.count else { return }
        selectedPromptIndex = index  // Set the index for editing
        currentPromptDialog = PromptEditDialogController(
            isEditing: true,
            existingPrompt: promptService.prompts[index],
            existingPromptNames: promptService.prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt in
            self.handleSavePrompt(name: name, prompt: prompt)
            self.currentPromptDialog = nil  // Release after save
        }
        currentPromptDialog?.showModal()
    }
    
    private func deleteSelectedPrompt() {
        guard let index = selectedPromptIndex else { return }
        
        let result = promptService.deletePrompt(at: index)
        switch result {
        case .success:
            selectedPromptIndex = nil
            notifyMenuUpdate()
        case .failure(let error):
            showErrorAlert(message: error.localizedDescription)
        }
    }
    
    private func confirmDeletePrompt() {
        guard selectedPromptIndex != nil else { return }
        deleteSelectedPrompt()
    }
    
    private func handleSavePrompt(name: String, prompt: String) {
        let wasEditingSelectedPrompt = selectedPromptIndex.map { promptService.prompts[$0].name } == getCurrentlySelectedPromptName()
        
        let promptItem = PromptItem(name: name, prompt: prompt)
        let result = promptService.savePrompt(promptItem, at: selectedPromptIndex)
        
        switch result {
        case .success:
            // Persist selection through rename if editing
            updateGlobalSelection(from: wasEditingSelectedPrompt, to: name)
            selectedPromptIndex = nil
            notifyMenuUpdate()
        case .failure(let error):
            showErrorAlert(message: error.localizedDescription)
        }
    }
    
    private func showErrorAlert(message: String) {
        let alert = NSAlert()
        alert.messageText = "Error"
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
    
    private func getCurrentlySelectedPromptName() -> String? {
        return UserDefaults.standard.string(forKey: "current_prompt")
    }
    
    private func updateGlobalSelection(from wasSelected: Bool, to newName: String) {
        guard wasSelected else { return }
        UserDefaults.standard.set(newName, forKey: "current_prompt")
        PotterLogger.shared.info("settings", "🔄 Updated global selection to renamed prompt: \(newName)")
    }
    
    private func notifyMenuUpdate() {
        DispatchQueue.main.async {
            if let appDelegate = NSApplication.shared.delegate as? AppDelegate {
                Task { @MainActor in
                    appDelegate.menuBarManager?.updateMenu()
                }
            }
        }
    }
    
    private func showDeleteAllDataDialog() {
        let alert = NSAlert()
        alert.messageText = "Delete All Potter Data"
        alert.informativeText = "This will permanently delete all Potter data including prompts, API keys, and settings. This action cannot be undone."
        alert.alertStyle = .critical
        
        alert.addButton(withTitle: "Cancel")
        let deleteButton = alert.addButton(withTitle: "Wait (5s)")
        deleteButton.isEnabled = false
        
        // Make delete button red
        deleteButton.contentTintColor = .systemRed
        
        class CountdownHandler {
            var countdown = 5
            var timer: Timer?
            weak var button: NSButton?
            
            func start() {
                timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] timer in
                    guard let self = self else {
                        timer.invalidate()
                        return
                    }
                    
                    self.countdown -= 1
                    
                    if self.countdown > 0 {
                        self.button?.title = "Wait (\(self.countdown)s)"
                    } else {
                        self.button?.title = "Delete All"
                        self.button?.isEnabled = true
                        timer.invalidate()
                        self.timer = nil
                    }
                }
                
                if let timer = timer {
                    RunLoop.main.add(timer, forMode: .common)
                }
            }
            
            func stop() {
                timer?.invalidate()
                timer = nil
            }
        }
        
        let handler = CountdownHandler()
        handler.button = deleteButton
        handler.start()
        
        let response = alert.runModal()
        handler.stop()
        
        if response == .alertSecondButtonReturn && deleteButton.isEnabled {
            initializeFreshState()
            
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                let alert = NSAlert()
                alert.messageText = "Data Deleted"
                alert.informativeText = "All Potter data has been deleted. The app has been reset to its initial state."
                alert.addButton(withTitle: "OK")
                alert.runModal()
            }
        }
    }
    
    // MARK: - Fresh Initialization Logic
    private func initializeFreshState() {
        // 1. Reset prompts to defaults
        promptService.resetToDefaults()
        
        // 2. Clear UserDefaults
        let bundleId = Bundle.main.bundleIdentifier ?? "com.graydot.potter"
        UserDefaults.standard.removePersistentDomain(forName: bundleId)
        UserDefaults.standard.synchronize()
        
        // 3. Clear API keys
        switch StorageAdapter.shared.clearAllAPIKeys() {
        case .success:
            break
        case .failure(let error):
            PotterLogger.shared.error("settings", "❌ Failed to clear API keys: \(error.localizedDescription)")
        }
        
        // 4. Reset settings to defaults
        settings.resetToDefaults()
        
        // 5. Reset hotkey to default
        UserDefaults.standard.set(HotkeyConstants.defaultHotkey, forKey: HotkeyConstants.userDefaultsKey)
        
        // 6. Update global hotkey system
        if let appDelegate = NSApplication.shared.delegate as? AppDelegate {
            Task { @MainActor in
                appDelegate.potterCore?.updateHotkey(HotkeyConstants.defaultHotkey)
            }
        }
    }
    
    // MARK: - Delete All Data Functions
    private func getPromptsFileURL() -> URL {
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let potterDir = appSupport.appendingPathComponent("Potter")
        return potterDir.appendingPathComponent("prompts.json")
    }
    
    private func openPromptsFolder() {
        let promptsFileURL = getPromptsFileURL()
        let parentDir = promptsFileURL.deletingLastPathComponent()
        NSWorkspace.shared.open(parentDir)
    }
    
    
    // API key management is now handled by LLMProviderView
}

// MARK: - Hotkey Configuration View
@available(macOS 14.0, *)
struct HotkeyConfigurationView: View {
    @State private var isCapturingHotkey = false
    @State private var capturedKeys: [String] = []
    @State private var currentHotkey = HotkeyConstants.defaultHotkey
    @State private var previousHotkey = HotkeyConstants.defaultHotkey // Store previous combo for ESC
    @State private var warningMessage = ""
    @FocusState private var isKeyCaptureFocused: Bool
    
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
                            hotkeyPill(currentHotkey[index], isActive: false)
                                .onTapGesture {
                                    startHotkeyCapture()
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
        .onAppear {
            loadSavedHotkey()
        }
    }
    
    private func loadSavedHotkey() {
        if let savedHotkey = UserDefaults.standard.array(forKey: HotkeyConstants.userDefaultsKey) as? [String] {
            currentHotkey = savedHotkey
            previousHotkey = savedHotkey
            PotterLogger.shared.debug("settings", "🎹 Loaded saved hotkey: \(savedHotkey.joined(separator: "+"))")
        }
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
            potterCore.potterCore?.disableGlobalHotkey()
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
        
        // Save to UserDefaults
        UserDefaults.standard.set(currentHotkey, forKey: HotkeyConstants.userDefaultsKey)
        
        PotterLogger.shared.info("settings", "🎹 Applied new hotkey: \(currentHotkey.joined(separator: "+"))")
        
        // Update the global hotkey system (this will re-enable it with new combo)
        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore?.updateHotkey(currentHotkey)
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
            potterCore.potterCore?.enableGlobalHotkey()
        }
        
        PotterLogger.shared.debug("settings", "🎹 Cancelled hotkey capture - restored previous combo")
    }
    
    private func resetToDefault() {
        currentHotkey = HotkeyConstants.defaultHotkey
        previousHotkey = HotkeyConstants.defaultHotkey
        warningMessage = ""
        capturedKeys.removeAll()
        isCapturingHotkey = false
        isKeyCaptureFocused = false
        
        // Save to UserDefaults
        UserDefaults.standard.set(currentHotkey, forKey: HotkeyConstants.userDefaultsKey)
        
        PotterLogger.shared.info("settings", "🎹 Reset hotkey to default: \(currentHotkey.joined(separator: "+"))")
        
        // Update the global hotkey system
        if let potterCore = NSApplication.shared.delegate as? AppDelegate {
            potterCore.potterCore?.updateHotkey(currentHotkey)
        }
    }
}


