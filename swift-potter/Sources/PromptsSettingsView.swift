import SwiftUI
import AppKit

@available(macOS 14.0, *)
struct PromptsSettingsView: View {
    @StateObject private var promptService = PromptService.shared
    @State private var selectedPromptID: UUID? = nil
    @State private var showingDeleteConfirmation = false
    @State private var currentPromptDialog: PromptEditDialogController? = nil

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
                    deleteSelectedPrompt()
                }
                .buttonStyle(.bordered)
                .disabled(selectedPromptID == nil || promptService.prompts.count <= 1)

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

            // Scrollable rows
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
                            selectedPromptID == promptItem.id ?
                            Color.accentColor.opacity(0.1) :
                            Color(NSColor.textBackgroundColor)
                        )
                        .simultaneousGesture(
                            TapGesture(count: 2)
                                .onEnded {
                                    selectedPromptID = promptItem.id
                                    editPrompt(at: index)
                                }
                        )
                        .simultaneousGesture(
                            TapGesture(count: 1)
                                .onEnded {
                                    selectedPromptID = promptItem.id
                                }
                        )

                        if index < promptService.prompts.count - 1 {
                            Divider()
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
        guard let id = selectedPromptID else { return nil }
        return promptService.prompts.first { $0.id == id }
    }

    private var selectedIndex: Int? {
        guard let id = selectedPromptID else { return nil }
        return promptService.prompts.firstIndex { $0.id == id }
    }

    // MARK: - Prompt Management

    private func addNewPrompt() {
        selectedPromptID = nil
        currentPromptDialog = PromptEditDialogController(
            isEditing: false,
            existingPrompt: nil,
            existingPromptNames: promptService.prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt in
            self.handleSavePrompt(name: name, prompt: prompt, editIndex: nil)
            self.currentPromptDialog = nil
        }
        currentPromptDialog?.showModal()
    }

    private func editPrompt(at index: Int) {
        guard index < promptService.prompts.count else { return }
        selectedPromptID = promptService.prompts[index].id
        currentPromptDialog = PromptEditDialogController(
            isEditing: true,
            existingPrompt: promptService.prompts[index],
            existingPromptNames: promptService.prompts.map { $0.name }
        )
        currentPromptDialog?.onSave = { name, prompt in
            self.handleSavePrompt(name: name, prompt: prompt, editIndex: index)
            self.currentPromptDialog = nil
        }
        currentPromptDialog?.showModal()
    }

    private func deleteSelectedPrompt() {
        guard let index = selectedIndex else { return }

        let result = promptService.deletePrompt(at: index)
        switch result {
        case .success:
            selectedPromptID = nil
            SettingsHelpers.notifyMenuUpdate()
        case .failure(let error):
            SettingsHelpers.showErrorAlert(message: error.localizedDescription)
        }
    }

    private func confirmDeletePrompt() {
        guard selectedIndex != nil else { return }
        deleteSelectedPrompt()
    }

    private func handleSavePrompt(name: String, prompt: String, editIndex: Int?) {
        let wasEditingSelectedPrompt = editIndex.flatMap { idx in
            promptService.prompts[idx].name
        }.map { $0 == getCurrentlySelectedPromptName() } ?? false

        let promptItem = PromptItem(name: name, prompt: prompt)
        let result = promptService.savePrompt(promptItem, at: editIndex)

        switch result {
        case .success:
            if wasEditingSelectedPrompt {
                UserDefaults.standard.set(name, forKey: "current_prompt")
                PotterLogger.shared.info("settings", "🔄 Updated global selection to renamed prompt: \(name)")
            }
            selectedPromptID = nil
            SettingsHelpers.notifyMenuUpdate()
        case .failure(let error):
            SettingsHelpers.showErrorAlert(message: error.localizedDescription)
        }
    }

    private func getCurrentlySelectedPromptName() -> String? {
        return UserDefaults.standard.string(forKey: "current_prompt")
    }
}
