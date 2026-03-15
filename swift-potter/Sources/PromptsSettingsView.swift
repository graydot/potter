import SwiftUI
import AppKit

@available(macOS 14.0, *)
struct PromptsSettingsView: View {
    @StateObject private var promptService = PromptService.shared
    // Persistent UI state: selection + scroll anchor survive window resizes and
    // section switches because they live in UIStateStore (backed by UserDefaults).
    @EnvironmentObject private var uiState: UIStateStore
    // Ephemeral interaction state: these are fine as @State because they only
    // matter while the user is actively interacting.
    @State private var showingDeleteConfirmation = false
    @State private var currentPromptDialog: PromptEditDialogController? = nil
    @State private var scrollProxy: ScrollViewProxy? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Prompts")
                .font(.title)
                .fontWeight(.semibold)

            Text("Customize the AI prompts used for text processing")
                .foregroundColor(.secondary)

            Text("Double-click to edit. Use + and - buttons to add/remove.")
                .foregroundColor(.secondary)
                .font(.caption)

            promptsTable
                .frame(minHeight: 150, maxHeight: .infinity)

            HStack {
                Button("+") {
                    addNewPrompt()
                }
                .buttonStyle(.bordered)

                Button("-") {
                    showingDeleteConfirmation = true
                }
                .buttonStyle(.bordered)
                .disabled(uiState.selectedPromptID == nil || promptService.prompts.count <= 1)

                Spacer()

                Text("\(promptService.prompts.count) prompts")
                    .foregroundColor(.secondary)
                    .font(.caption)
            }

        }
        .alert("Delete Prompt", isPresented: $showingDeleteConfirmation) {
            Button("Delete", role: .destructive) {
                confirmDeletePrompt()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            if let prompt = selectedPrompt {
                Text("Are you sure you want to delete the prompt '\(prompt.name)'? This action cannot be undone.")
            }
        }
    }

    private var promptsTable: some View {
        VStack(spacing: 0) {
            // Fixed header
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

            // Scrollable rows — scroll position is preserved across window resizes
            // because scrollAnchorID lives in UIStateStore, not local @State.
            GeometryReader { containerGeometry in
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 0) {
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
                                    uiState.selectedPromptID == promptItem.id ?
                                    Color.accentColor.opacity(0.1) :
                                    Color(NSColor.textBackgroundColor)
                                )
                                .id(promptItem.id)
                                // On first appearance, seed the anchor to the first visible item
                                // so a subsequent resize has something to scroll back to.
                                .onAppear {
                                    if uiState.scrollAnchorID == nil {
                                        uiState.scrollAnchorID = promptItem.id
                                    }
                                }
                                .simultaneousGesture(
                                    TapGesture(count: 2)
                                        .onEnded {
                                            uiState.selectedPromptID = promptItem.id
                                            editPrompt(at: index)
                                        }
                                )
                                .simultaneousGesture(
                                    TapGesture(count: 1)
                                        .onEnded {
                                            uiState.selectedPromptID = promptItem.id
                                            // Update scroll anchor so resize restores to the
                                            // item the user last interacted with.
                                            uiState.scrollAnchorID = promptItem.id
                                        }
                                )

                                if index < promptService.prompts.count - 1 {
                                    Divider()
                                }
                            }
                        }
                    }
                    .onAppear {
                        scrollProxy = proxy
                        // Restore scroll position on re-appearance (e.g. switching
                        // back to the Prompts tab after visiting another section).
                        if let anchor = uiState.scrollAnchorID {
                            proxy.scrollTo(anchor, anchor: .top)
                        }
                    }
                    // When the container dimensions change (window resize), scroll
                    // back to the last known anchor item so the position is preserved.
                    .onChange(of: containerGeometry.size) { _ in
                        if let anchor = uiState.scrollAnchorID {
                            proxy.scrollTo(anchor, anchor: .top)
                        }
                    }
                }
            }
        }
        .background(Color(NSColor.textBackgroundColor))
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .stroke(Color(NSColor.separatorColor))
        )
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }

    // MARK: - Selected Prompt Helpers

    private var selectedPrompt: PromptItem? {
        guard let id = uiState.selectedPromptID else { return nil }
        return promptService.prompts.first { $0.id == id }
    }

    private var selectedIndex: Int? {
        guard let id = uiState.selectedPromptID else { return nil }
        return promptService.prompts.firstIndex { $0.id == id }
    }

    // MARK: - Prompt Management

    private func addNewPrompt() {
        uiState.selectedPromptID = nil
        currentPromptDialog = PromptEditDialogController(
            isEditing: false,
            existingPrompt: nil,
            existingPromptNames: promptService.prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt, tier, outputMode in
            self.handleSavePrompt(name: name, prompt: prompt, modelTier: tier, outputMode: outputMode, editIndex: nil)
            self.currentPromptDialog = nil
        }
        currentPromptDialog?.showModal()
    }

    private func editPrompt(at index: Int) {
        guard index < promptService.prompts.count else { return }
        uiState.selectedPromptID = promptService.prompts[index].id
        currentPromptDialog = PromptEditDialogController(
            isEditing: true,
            existingPrompt: promptService.prompts[index],
            existingPromptNames: promptService.prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt, tier, outputMode in
            self.handleSavePrompt(name: name, prompt: prompt, modelTier: tier, outputMode: outputMode, editIndex: index)
            self.currentPromptDialog = nil
        }
        currentPromptDialog?.showModal()
    }

    private func deleteSelectedPrompt() {
        guard let index = selectedIndex else { return }

        let result = promptService.deletePrompt(at: index)
        switch result {
        case .success:
            uiState.selectedPromptID = nil
            SettingsHelpers.notifyMenuUpdate()
        case .failure(let error):
            SettingsHelpers.showErrorAlert(message: error.localizedDescription)
        }
    }

    private func confirmDeletePrompt() {
        guard selectedIndex != nil else { return }
        deleteSelectedPrompt()
    }

    private func handleSavePrompt(name: String, prompt: String, modelTier: ModelTier? = nil, outputMode: OutputMode = .replace, editIndex: Int?) {
        let wasEditingSelectedPrompt = editIndex.flatMap { idx in
            promptService.prompts[idx].name
        }.map { $0 == getCurrentlySelectedPromptName() } ?? false

        let promptItem = PromptItem(name: name, prompt: prompt, modelTier: modelTier, outputMode: outputMode)
        let result = promptService.savePrompt(promptItem, at: editIndex)

        switch result {
        case .success:
            if editIndex == nil {
                // New prompt: set it as the current prompt so it's immediately usable
                UserDefaults.standard.set(name, forKey: UserDefaultsKeys.currentPrompt)
                promptService.setCurrentPrompt(name)
                PotterLogger.shared.info("settings", "📌 Set newly created prompt as current: \(name)")
            } else if wasEditingSelectedPrompt {
                UserDefaults.standard.set(name, forKey: UserDefaultsKeys.currentPrompt)
                PotterLogger.shared.info("settings", "🔄 Updated global selection to renamed prompt: \(name)")
            }
            uiState.selectedPromptID = nil
            SettingsHelpers.notifyMenuUpdate()
        case .failure(let error):
            SettingsHelpers.showErrorAlert(message: error.localizedDescription)
        }
    }

    private func getCurrentlySelectedPromptName() -> String? {
        return UserDefaults.standard.string(forKey: UserDefaultsKeys.currentPrompt)
    }
}
