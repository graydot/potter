import SwiftUI
import AppKit

// MARK: - Permissions Configuration View
struct PermissionsView: View {
    @StateObject private var permissionManager = PermissionManager.shared
    @State private var showingResetConfirmation = false
    @State private var isResettingPermissions = false
    @State private var notificationsEnabled = true
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Combined Accessibility + Hotkey Section
            combinedAccessibilitySection
            
            // Combined Notifications Section
            combinedNotificationsSection
            
            Divider()
                .padding(.vertical, 8)
            
            // Reset Permissions Section
            resetPermissionsSection
        }
        .onAppear {
            permissionManager.checkAllPermissions()
            // Load notifications setting
            notificationsEnabled = UserDefaults.standard.bool(forKey: "notifications_enabled")
        }
        .confirmationDialog(
            "Reset All Permissions",
            isPresented: $showingResetConfirmation,
            titleVisibility: .visible
        ) {
            Button("Reset", role: .destructive) {
                resetPermissions()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This will remove ALL permissions for Potter from System Settings. You will need to re-grant permissions and restart the app.")
        }
    }
    
    // MARK: - Permission Row
    private func permissionRow(for permission: PermissionType) -> some View {
        let status = permissionManager.getPermissionStatus(for: permission)
        
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Permission Icon and Name
                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 2) {
                        HStack {
                            Text(permission.displayName)
                                .fontWeight(.medium)
                            
                            if permission.isRequired {
                                Text("(Required)")
                                    .font(.caption)
                                    .foregroundColor(.orange)
                                    .fontWeight(.medium)
                            }
                        }
                        
                        Text(permission.description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                // Status and Action
                HStack(spacing: 12) {
                    // Status Text
                    Text(status.displayText)
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundColor(Color(status.color))
                    
                    // Loading Spinner
                    if permissionManager.isCheckingPermissions {
                        ProgressView()
                            .scaleEffect(0.6)
                            .frame(width: 16, height: 16)
                    }
                    
                    // Action Button
                    Button(actionButtonText(for: permission, status: status)) {
                        handlePermissionAction(for: permission, status: status)
                    }
                    .buttonStyle(.bordered)
                    .disabled(permission == .notifications && !notificationsEnabled)
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
                    .stroke(Color(status.color).opacity(0.3), lineWidth: 1)
            )
        }
    }
    
    // MARK: - Reset Permissions Section
    private var resetPermissionsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Reset Permissions")
                .font(.headline)
                .fontWeight(.semibold)
            
            Text("Remove all permissions for Potter from System Settings. This will require re-granting permissions and restarting the app.")
                .font(.caption)
                .foregroundColor(.secondary)
                .fixedSize(horizontal: false, vertical: true)
            
            HStack {
                Button("Reset All Permissions") {
                    showingResetConfirmation = true
                }
                .buttonStyle(.bordered)
                .disabled(isResettingPermissions)
                
                if isResettingPermissions {
                    ProgressView()
                        .scaleEffect(0.7)
                        .frame(width: 20, height: 20)
                    
                    Text("Resetting...")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
            }
        }
        .padding(.vertical, 8)
        .padding(.horizontal, 12)
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.orange.opacity(0.1))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .stroke(Color.orange.opacity(0.3), lineWidth: 1)
        )
    }
    
    // MARK: - Combined Accessibility + Hotkey Section
    private var combinedAccessibilitySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Accessibility permission
            accessibilityPermissionContent
            
            // Divider between permission and hotkey
            Divider()
                .opacity(0.5)
            
            // Hotkey Configuration (below accessibility)
            if #available(macOS 14.0, *) {
                HotkeyConfigurationView()
            } else {
                // Fallback for older macOS versions
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("Global Hotkey:")
                            .fontWeight(.medium)
                        Text("⌘⇧R")
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
                .stroke(Color.green.opacity(0.3), lineWidth: 1)
        )
    }
    
    // MARK: - Accessibility Permission Content (without background)
    private var accessibilityPermissionContent: some View {
        let status = permissionManager.getPermissionStatus(for: .accessibility)
        
        return HStack {
            // Permission Icon and Name
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text(PermissionType.accessibility.displayName)
                            .fontWeight(.medium)
                        
                        if PermissionType.accessibility.isRequired {
                            Text("(Required)")
                                .font(.caption)
                                .foregroundColor(.orange)
                                .fontWeight(.medium)
                        }
                    }
                    
                    Text(PermissionType.accessibility.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    // Help text when accessibility is not granted
                    if status == .denied {
                        Text("You can still use this app without accessibility permissions by clicking menu bar items to process text")
                            .font(.caption2)
                            .foregroundColor(.orange)
                            .padding(.top, 4)
                    }
                }
            }
            
            Spacer()
            
            // Status and Action
            HStack(spacing: 12) {
                // Status Text
                Text(status.displayText)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(Color(status.color))
                
                // Loading Spinner
                if permissionManager.isCheckingPermissions {
                    ProgressView()
                        .scaleEffect(0.6)
                        .frame(width: 16, height: 16)
                }
                
                // Action Button
                Button(actionButtonText(for: .accessibility, status: status)) {
                    handlePermissionAction(for: .accessibility, status: status)
                }
                .buttonStyle(.bordered)
            }
        }
    }
    
    // MARK: - Combined Notifications Section
    private var combinedNotificationsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Notifications preference toggle
            HStack {
                // Notification Icon and Name
                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Show Notifications")
                            .fontWeight(.medium)
                        
                        Text("Display status messages and alerts")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                // Toggle Switch
                Toggle("", isOn: $notificationsEnabled)
                    .labelsHidden()
                    .toggleStyle(SwitchToggleStyle())
                    .onChange(of: notificationsEnabled) { newValue in
                        // Save to UserDefaults
                        UserDefaults.standard.set(newValue, forKey: "notifications_enabled")
                        PotterLogger.shared.info("settings", "📱 Notifications enabled: \(newValue)")
                        
                        // Re-check permissions when notifications are enabled
                        if newValue {
                            permissionManager.checkAllPermissions()
                        }
                    }
            }
            
            // Divider between toggle and permission
            Divider()
                .opacity(0.5)
            
            // Notifications permission
            notificationPermissionContent
                .opacity(!notificationsEnabled ? 0.5 : 1.0)
                .disabled(!notificationsEnabled)
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
    
    // MARK: - Notification Permission Content (without background)
    private var notificationPermissionContent: some View {
        let status = permissionManager.getPermissionStatus(for: .notifications)
        
        return HStack {
            // Permission Icon and Name
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text(PermissionType.notifications.displayName)
                            .fontWeight(.medium)
                        
                        if PermissionType.notifications.isRequired {
                            Text("(Required)")
                                .font(.caption)
                                .foregroundColor(.orange)
                                .fontWeight(.medium)
                        }
                    }
                    
                    Text(PermissionType.notifications.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            // Status and Action
            HStack(spacing: 12) {
                // Status Text
                Text(status.displayText)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(Color(status.color))
                
                // Loading Spinner
                if permissionManager.isCheckingPermissions {
                    ProgressView()
                        .scaleEffect(0.6)
                        .frame(width: 16, height: 16)
                }
                
                // Action Button
                Button(actionButtonText(for: .notifications, status: status)) {
                    handlePermissionAction(for: .notifications, status: status)
                }
                .buttonStyle(.bordered)
                .disabled(!notificationsEnabled)
            }
        }
    }
    
    // MARK: - Notifications Preference Row (Legacy - keeping for reference)
    private var notificationsPreferenceRow: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                // Notification Icon and Name
                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Show Notifications")
                            .fontWeight(.medium)
                        
                        Text("Display status messages and alerts")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                
                Spacer()
                
                // Toggle Switch
                Toggle("", isOn: $notificationsEnabled)
                    .labelsHidden()
                    .toggleStyle(SwitchToggleStyle())
                    .onChange(of: notificationsEnabled) { newValue in
                        // Save to UserDefaults
                        UserDefaults.standard.set(newValue, forKey: "notifications_enabled")
                        PotterLogger.shared.info("settings", "📱 Notifications enabled: \(newValue)")
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
    
    // MARK: - Helper Methods
    private func actionButtonText(for permission: PermissionType, status: PermissionStatus) -> String {
        switch status {
        case .granted:
            return "Open Settings"
        case .denied, .notDetermined, .unknown:
            return "Open Settings"
        }
    }
    
    private func handlePermissionAction(for permission: PermissionType, status: PermissionStatus) {
        switch permission {
        case .accessibility:
            if status == .granted {
                permissionManager.openSystemSettings(for: .accessibility)
            } else {
                permissionManager.requestAccessibilityPermission()
            }
            
        case .notifications:
            if status == .granted {
                permissionManager.openSystemSettings(for: .notifications)
            } else if status == .notDetermined {
                permissionManager.requestNotificationPermission()
            } else {
                permissionManager.openSystemSettings(for: .notifications)
            }
        }
    }
    
    private func resetPermissions() {
        isResettingPermissions = true
        
        Task {
            let success = await permissionManager.resetAllPermissions()
            
            await MainActor.run {
                isResettingPermissions = false
                
                if success {
                    // Prompt for restart after successful reset
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        permissionManager.promptForRestart()
                    }
                } else {
                    let alert = NSAlert()
                    alert.messageText = "Reset Failed"
                    alert.informativeText = "Failed to reset permissions. You may need to manually remove Potter from System Settings."
                    alert.addButton(withTitle: "OK")
                    alert.runModal()
                }
            }
        }
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
struct PermissionsView_Previews: PreviewProvider {
    static var previews: some View {
        PermissionsView()
            .frame(width: 600, height: 400)
            .padding()
    }
}