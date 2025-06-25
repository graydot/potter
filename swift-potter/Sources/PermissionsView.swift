import SwiftUI
import AppKit

// MARK: - Hotkey Configuration View  
struct HotkeyView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Hotkey Section
            hotkeySection
        }
    }
    
    
    
    // MARK: - Hotkey Section
    private var hotkeySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Hotkey Configuration
            if #available(macOS 14.0, *) {
                HotkeyConfigurationView()
            } else {
                // Fallback for older macOS versions
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Global Hotkey:")
                            .fontWeight(.medium)
                        Text("⌘⇧9")
                            .font(.system(.body, design: .monospaced))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 2)
                            .background(Color.secondary.opacity(0.2))
                            .cornerRadius(4)
                        Spacer()
                        Text("(Requires macOS 14+)")
                            .foregroundColor(.secondary)
                            .font(.caption)
                    }
                }
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(NSColor.controlBackgroundColor).opacity(0.5))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.blue.opacity(0.3), lineWidth: 1)
        )
    }
    
    
}

// MARK: - Permission Status Summary
struct PermissionStatusSummary: View {
    @StateObject private var permissionManager = PermissionManager.shared
    
    var body: some View {
        HStack(spacing: 16) {
            ForEach(PermissionType.allCases, id: \.self) { permission in
                let status = permissionManager.getPermissionStatus(for: permission)
                
                HStack(spacing: 6) {
                    Image(systemName: status.iconName)
                        .foregroundColor(Color(status.color))
                        .font(.caption)
                    
                    Text(permission.displayName)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .onAppear {
            permissionManager.checkAllPermissions()
        }
    }
}

// MARK: - Preview
struct HotkeyView_Previews: PreviewProvider {
    static var previews: some View {
        HotkeyView()
            .frame(width: 600, height: 400)
            .padding()
    }
}