#!/usr/bin/env python3
"""
Settings UI for Rephrasely - macOS style preferences window
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
from typing import Dict, Any
import threading

class SettingsManager:
    """Manages saving and loading of user settings"""
    
    def __init__(self, settings_file="config/settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "prompts": {
                'rephrase': 'Please rephrase the following text to make it clearer and more professional:',
                'summarize': 'Please provide a concise summary of the following text:',
                'expand': 'Please expand on the following text with more detail and examples:',
                'casual': 'Please rewrite the following text in a more casual, friendly tone:',
                'formal': 'Please rewrite the following text in a more formal, professional tone:'
            },
            "hotkey": "cmd+shift+r",
            "model": "gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "auto_paste": True,
            "show_notifications": True
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file, create default if not exists"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            self.settings = settings
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        self.settings[key] = value

class SettingsWindow:
    """Main settings window with tabbed interface"""
    
    def __init__(self, settings_manager: SettingsManager, on_settings_changed=None):
        self.settings_manager = settings_manager
        self.on_settings_changed = on_settings_changed
        self.window = None
        self.prompt_widgets = {}
        
    def show(self):
        """Show the settings window"""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            return
        
        self.create_window()
    
    def create_window(self):
        """Create the main settings window"""
        self.window = tk.Toplevel()
        self.window.title("Rephrasely Preferences")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Make it look more native on macOS
        try:
            # Try to set macOS-specific window properties
            self.window.tk.call('::tk::unsupported::MacWindowStyle', 'style', self.window._w, 'document', 'noTitleBar')
        except:
            pass
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Create tabs
        self.create_prompts_tab()
        self.create_general_tab()
        self.create_advanced_tab()
        
        # Create buttons frame
        self.create_buttons_frame()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Center the window
        self.center_window()
    
    def create_prompts_tab(self):
        """Create the prompts customization tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Prompts")
        
        # Configure grid
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(frame, text="Customize AI Prompts", font=("SF Pro Display", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(10, 20), sticky="w")
        
        # Create scrollable frame for prompts
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Create prompt editors
        prompts = self.settings_manager.get("prompts", {})
        
        for i, (mode, prompt) in enumerate(prompts.items()):
            self.create_prompt_editor(scrollable_frame, i, mode, prompt)
    
    def create_prompt_editor(self, parent, row, mode, prompt):
        """Create a prompt editor for a specific mode"""
        # Mode label
        mode_frame = ttk.LabelFrame(parent, text=f"{mode.title()} Mode", padding=10)
        mode_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        mode_frame.grid_columnconfigure(0, weight=1)
        
        # Prompt text area
        text_widget = scrolledtext.ScrolledText(
            mode_frame, 
            height=4, 
            wrap=tk.WORD,
            font=("SF Mono", 11)
        )
        text_widget.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        text_widget.insert("1.0", prompt)
        
        # Store reference
        self.prompt_widgets[mode] = text_widget
        
        # Reset button
        reset_btn = ttk.Button(
            mode_frame, 
            text="Reset to Default",
            command=lambda m=mode: self.reset_prompt(m)
        )
        reset_btn.grid(row=1, column=0, sticky="e")
    
    def create_general_tab(self):
        """Create the general settings tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="General")
        
        # Configure grid
        frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(frame, text="General Settings", font=("SF Pro Display", 16, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(10, 20), sticky="w")
        row += 1
        
        # Hotkey setting
        ttk.Label(frame, text="Global Hotkey:").grid(row=row, column=0, sticky="w", padx=(10, 20), pady=5)
        self.hotkey_var = tk.StringVar(value=self.settings_manager.get("hotkey", "cmd+shift+r"))
        hotkey_entry = ttk.Entry(frame, textvariable=self.hotkey_var, width=20)
        hotkey_entry.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Auto-paste setting
        self.auto_paste_var = tk.BooleanVar(value=self.settings_manager.get("auto_paste", True))
        auto_paste_check = ttk.Checkbutton(
            frame, 
            text="Automatically paste processed text", 
            variable=self.auto_paste_var
        )
        auto_paste_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        row += 1
        
        # Show notifications setting
        self.notifications_var = tk.BooleanVar(value=self.settings_manager.get("show_notifications", True))
        notifications_check = ttk.Checkbutton(
            frame, 
            text="Show success/error notifications", 
            variable=self.notifications_var
        )
        notifications_check.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        row += 1
    
    def create_advanced_tab(self):
        """Create the advanced settings tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Advanced")
        
        # Configure grid
        frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(frame, text="Advanced Settings", font=("SF Pro Display", 16, "bold"))
        title_label.grid(row=row, column=0, columnspan=2, pady=(10, 20), sticky="w")
        row += 1
        
        # Model selection
        ttk.Label(frame, text="AI Model:").grid(row=row, column=0, sticky="w", padx=(10, 20), pady=5)
        self.model_var = tk.StringVar(value=self.settings_manager.get("model", "gpt-3.5-turbo"))
        model_combo = ttk.Combobox(
            frame, 
            textvariable=self.model_var,
            values=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
            width=20,
            state="readonly"
        )
        model_combo.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Max tokens
        ttk.Label(frame, text="Max Tokens:").grid(row=row, column=0, sticky="w", padx=(10, 20), pady=5)
        self.max_tokens_var = tk.StringVar(value=str(self.settings_manager.get("max_tokens", 1000)))
        max_tokens_entry = ttk.Entry(frame, textvariable=self.max_tokens_var, width=20)
        max_tokens_entry.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Temperature
        ttk.Label(frame, text="Temperature:").grid(row=row, column=0, sticky="w", padx=(10, 20), pady=5)
        self.temperature_var = tk.StringVar(value=str(self.settings_manager.get("temperature", 0.7)))
        temperature_entry = ttk.Entry(frame, textvariable=self.temperature_var, width=20)
        temperature_entry.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        # Export/Import buttons
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        row += 1
        
        export_btn = ttk.Button(frame, text="Export Settings", command=self.export_settings)
        export_btn.grid(row=row, column=0, sticky="w", padx=10, pady=5)
        
        import_btn = ttk.Button(frame, text="Import Settings", command=self.import_settings)
        import_btn.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
    
    def create_buttons_frame(self):
        """Create the bottom buttons frame"""
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        button_frame.grid_columnconfigure(2, weight=1)
        
        # Cancel button
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_close)
        cancel_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Apply button
        apply_btn = ttk.Button(button_frame, text="Apply", command=self.apply_settings)
        apply_btn.grid(row=0, column=1, padx=(0, 10))
        
        # Save button
        save_btn = ttk.Button(button_frame, text="Save", command=self.save_settings)
        save_btn.grid(row=0, column=3)
    
    def reset_prompt(self, mode):
        """Reset a prompt to its default value"""
        default_prompt = self.settings_manager.default_settings["prompts"].get(mode, "")
        if mode in self.prompt_widgets:
            text_widget = self.prompt_widgets[mode]
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", default_prompt)
    
    def apply_settings(self):
        """Apply settings without saving to file"""
        settings = self.collect_settings()
        self.settings_manager.settings = settings
        
        if self.on_settings_changed:
            self.on_settings_changed(settings)
        
        messagebox.showinfo("Applied", "Settings applied successfully!")
    
    def save_settings(self):
        """Save settings to file and apply them"""
        settings = self.collect_settings()
        
        if self.settings_manager.save_settings(settings):
            if self.on_settings_changed:
                self.on_settings_changed(settings)
            messagebox.showinfo("Saved", "Settings saved successfully!")
            self.on_close()
        else:
            messagebox.showerror("Error", "Failed to save settings!")
    
    def collect_settings(self):
        """Collect all settings from the UI"""
        settings = self.settings_manager.settings.copy()
        
        # Collect prompts
        prompts = {}
        for mode, text_widget in self.prompt_widgets.items():
            prompts[mode] = text_widget.get("1.0", tk.END).strip()
        settings["prompts"] = prompts
        
        # Collect general settings
        settings["hotkey"] = self.hotkey_var.get()
        settings["auto_paste"] = self.auto_paste_var.get()
        settings["show_notifications"] = self.notifications_var.get()
        
        # Collect advanced settings
        settings["model"] = self.model_var.get()
        try:
            settings["max_tokens"] = int(self.max_tokens_var.get())
        except ValueError:
            settings["max_tokens"] = 1000
        
        try:
            settings["temperature"] = float(self.temperature_var.get())
        except ValueError:
            settings["temperature"] = 0.7
        
        return settings
    
    def export_settings(self):
        """Export settings to a file"""
        filename = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            settings = self.collect_settings()
            try:
                with open(filename, 'w') as f:
                    json.dump(settings, f, indent=2)
                messagebox.showinfo("Exported", f"Settings exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export settings: {e}")
    
    def import_settings(self):
        """Import settings from a file"""
        filename = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    imported_settings = json.load(f)
                
                # Update UI with imported settings
                self.load_settings_to_ui(imported_settings)
                messagebox.showinfo("Imported", f"Settings imported from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import settings: {e}")
    
    def load_settings_to_ui(self, settings):
        """Load settings into the UI components"""
        # Load prompts
        prompts = settings.get("prompts", {})
        for mode, text_widget in self.prompt_widgets.items():
            if mode in prompts:
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", prompts[mode])
        
        # Load general settings
        self.hotkey_var.set(settings.get("hotkey", "cmd+shift+r"))
        self.auto_paste_var.set(settings.get("auto_paste", True))
        self.notifications_var.set(settings.get("show_notifications", True))
        
        # Load advanced settings
        self.model_var.set(settings.get("model", "gpt-3.5-turbo"))
        self.max_tokens_var.set(str(settings.get("max_tokens", 1000)))
        self.temperature_var.set(str(settings.get("temperature", 0.7)))
    
    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_close(self):
        """Handle window close"""
        self.window.destroy()
        self.window = None

def show_settings(settings_manager, on_settings_changed=None):
    """Show the settings window"""
    # Run in main thread
    def show_ui():
        window = SettingsWindow(settings_manager, on_settings_changed)
        window.show()
    
    # If we're in a thread, schedule on main thread
    try:
        import tkinter
        root = tkinter._default_root
        if root:
            root.after(0, show_ui)
        else:
            show_ui()
    except:
        show_ui()

# Test the UI if run directly
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    settings_manager = SettingsManager()
    window = SettingsWindow(settings_manager)
    window.show()
    
    root.mainloop() 