import SwiftUI
import AppKit

// MARK: - Custom Window for ESC Handling
class SettingsWindow: NSWindow {
    override func keyDown(with event: NSEvent) {
        if event.keyCode == 53 {
            close()
        } else {
            super.keyDown(with: event)
        }
    }

    override func close() {
        super.close()
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

        if #available(macOS 14.0, *) {
            let settingsView = ModernSettingsView()
            let hostingView = NSHostingView(rootView: settingsView)
            window.contentView = hostingView
        } else {
            fatalError("macOS 14.0+ required")
        }
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func showWindow(_ sender: Any?) {
        NSApp.setActivationPolicy(.regular)
        super.showWindow(sender)
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    override func close() {
        super.close()
        NSApp.setActivationPolicy(.accessory)
    }
}

@available(macOS 14.0, *)
struct ModernSettingsView: View {
    // UIStateStore owns all persistent UI state (selected section, sidebar width,
    // scroll positions, list selections).  It is created once here and injected
    // into every child view via the environment so that state is never lost when
    // SwiftUI rebuilds the view hierarchy on a window resize.
    @StateObject private var uiState = UIStateStore.shared
    @Environment(\.colorScheme) var colorScheme
    @State private var isDraggingDivider = false

    let sections = [
        ("General", "gear"),
        ("Prompts", "bubble.left.and.bubble.right"),
        ("Updates", "arrow.down.circle"),
        ("About", "info.circle"),
        ("Logs", "list.bullet.rectangle"),
        ("History", "clock.arrow.circlepath")
    ]

    private let sidebarMinWidth: Double = 180
    private let sidebarMaxWidth: Double = 300

    var body: some View {
        GeometryReader { geometry in
            HStack(spacing: 0) {
                sidebar
                    .frame(width: CGFloat(uiState.sidebarWidth))

                // Draggable divider
                Rectangle()
                    .fill(isDraggingDivider
                          ? Color.accentColor.opacity(0.4)
                          : Color(NSColor.separatorColor))
                    .frame(width: 1)
                    .contentShape(Rectangle().inset(by: -4))
                    .gesture(
                        DragGesture(minimumDistance: 1)
                            .onChanged { value in
                                isDraggingDivider = true
                                let newWidth = uiState.sidebarWidth + value.translation.width
                                uiState.sidebarWidth = min(sidebarMaxWidth,
                                                           max(sidebarMinWidth, newWidth))
                            }
                            .onEnded { _ in
                                isDraggingDivider = false
                            }
                    )
                    .onHover { hovering in
                        if hovering {
                            NSCursor.resizeLeftRight.push()
                        } else {
                            NSCursor.pop()
                        }
                    }

                mainContent
                    .frame(width: max(600,
                                     geometry.size.width - CGFloat(uiState.sidebarWidth) - 1))
            }
        }
        .background(Color(NSColor.windowBackgroundColor))
        // Inject UIStateStore into the entire settings view hierarchy so that
        // child views (Prompts, Logs, etc.) can access persistent UI state
        // without needing to pass it through explicit init parameters.
        .environmentObject(uiState)
    }

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 0) {
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

            VStack(alignment: .leading, spacing: 4) {
                ForEach(Array(sections.enumerated()), id: \.offset) { index, section in
                    Button(action: {
                        uiState.selectedSection = index
                    }) {
                        HStack {
                            Image(systemName: section.1)
                                .foregroundColor(uiState.selectedSection == index ? .white : .secondary)
                                .frame(width: 18)
                                .font(.system(size: 16))
                            Text(section.0)
                                .foregroundColor(uiState.selectedSection == index ? .white : .primary)
                                .font(.system(size: 15, weight: .medium))
                            Spacer()
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.leading, 16)
                        .padding(.trailing, 8)
                        .padding(.vertical, 12)
                        .background(
                            uiState.selectedSection == index ?
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
        .background(Color(NSColor.controlBackgroundColor))
    }

    private var mainContent: some View {
        VStack(alignment: .leading, spacing: 0) {
            switch uiState.selectedSection {
            case 0:
                GeneralSettingsView()
            case 1:
                PromptsSettingsView()
            case 2:
                UpdatesSettingsView()
            case 3:
                AboutSettingsView()
            case 4:
                LogsSettingsView()
            case 5:
                HistorySettingsView()
            default:
                GeneralSettingsView()
            }
        }
        .padding(uiState.selectedSection == 0 ? 0 : 20)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }
}
