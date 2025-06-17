#!/usr/bin/env python3
"""
Prompts Settings Section
Handles prompt management in settings
"""

import logging
import objc
from typing import Optional, Callable, List, Dict
from AppKit import (
    NSView, NSTableView, NSScrollView, NSTableColumn,
    NSMakeRect, NSFont, NSColor,
    NSViewWidthSizable, NSViewHeightSizable, NSBezelBorder,
    NSIndexSet,
    NSTableViewAnimationSlideDown, NSTableViewAnimationSlideUp
)
from Foundation import NSObject

from ..widgets.ui_helpers import create_label, create_button
from ..dialogs.prompt_dialog import PromptDialog
from ..validators.prompt_validator import PromptValidator

logger = logging.getLogger(__name__)


class PromptsTableDataSource(NSObject):
    """Data source for prompts table view"""
    
    def init(self):
        self = objc.super(PromptsTableDataSource, self).init()
        if self is None:
            return None
        self.prompts = []
        return self
        
    def set_prompts(self, prompts: List[Dict]):
        """Set the prompts data"""
        self.prompts = prompts
        
    def numberOfRowsInTableView_(self, table_view):
        """Return number of rows"""
        return len(self.prompts)
        
    def tableView_objectValueForTableColumn_row_(self, table_view, column, row):
        """Return value for specific cell"""
        if 0 <= row < len(self.prompts):
            prompt = self.prompts[row]
            identifier = column.identifier()
            
            if identifier == "name":
                return prompt.get("name", "")
            elif identifier == "text":
                text = prompt.get("text", "")
                return text[:50] + "..." if len(text) > 50 else text
                
        return ""


class PromptsSettingsSection:
    """Manages the prompts settings section"""
    
    def __init__(self, settings_manager, on_settings_changed: Optional[Callable] = None):
        """
        Initialize prompts settings section
        
        Args:
            settings_manager: Settings manager instance
            on_settings_changed: Callback when settings change
        """
        self.settings_manager = settings_manager
        self.on_settings_changed = on_settings_changed
        
        # UI elements
        self.view = None
        self.table_view = None
        self.scroll_view = None
        self.data_source = PromptsTableDataSource()
        self.add_button = None
        self.edit_button = None
        self.delete_button = None
        self.duplicate_button = None
        
        # Validator
        self.validator = PromptValidator()
        
    def create_view(self, width: int = 700, height: int = 600) -> NSView:
        """
        Create the prompts settings view
        
        Args:
            width: View width
            height: View height
            
        Returns:
            NSView containing the prompts settings
        """
        logger.debug("Creating prompts settings view")
        
        # Create main view
        self.view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))
        
        y_offset = height - 40
        
        # Title
        title = create_label(
            "Prompts",
            NSMakeRect(20, y_offset, 200, 30),
            font=NSFont.boldSystemFontOfSize_(18)
        )
        self.view.addSubview_(title)
        
        # Description
        y_offset -= 30
        desc = create_label(
            "Manage your text transformation prompts",
            NSMakeRect(20, y_offset, 600, 20),
            font=NSFont.systemFontOfSize_(13),
            color=NSColor.secondaryLabelColor()
        )
        self.view.addSubview_(desc)
        
        y_offset -= 40
        
        # Create table view
        table_height = 350
        self._create_table_view(20, y_offset - table_height, width - 40, table_height)
        
        y_offset -= table_height + 20
        
        # Create buttons
        self._create_buttons(20, y_offset)
        
        # Load prompts
        self._load_prompts()
        
        return self.view
        
    def _create_table_view(self, x: float, y: float, width: float, height: float):
        """Create the prompts table view"""
        # Create scroll view
        self.scroll_view = NSScrollView.alloc().initWithFrame_(
            NSMakeRect(x, y, width, height)
        )
        self.scroll_view.setHasVerticalScroller_(True)
        self.scroll_view.setHasHorizontalScroller_(False)
        self.scroll_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable
        )
        self.scroll_view.setBorderType_(NSBezelBorder)
        
        # Create table view
        self.table_view = NSTableView.alloc().initWithFrame_(
            NSMakeRect(0, 0, width, height)
        )
        self.table_view.setDataSource_(self.data_source)
        self.table_view.setDelegate_(self)
        self.table_view.setAllowsMultipleSelection_(False)
        self.table_view.setUsesAlternatingRowBackgroundColors_(True)
        
        # Create columns
        name_column = NSTableColumn.alloc().initWithIdentifier_("name")
        name_column.setTitle_("Name")
        name_column.setWidth_(150)
        name_column.setMinWidth_(100)
        name_column.setMaxWidth_(200)
        self.table_view.addTableColumn_(name_column)
        
        text_column = NSTableColumn.alloc().initWithIdentifier_("text")
        text_column.setTitle_("Prompt Text")
        text_column.setWidth_(width - 170)
        text_column.setMinWidth_(200)
        self.table_view.addTableColumn_(text_column)
        
        # Set table view as document view
        self.scroll_view.setDocumentView_(self.table_view)
        
        # Add to view
        self.view.addSubview_(self.scroll_view)
        
    def _create_buttons(self, x: float, y: float):
        """Create action buttons"""
        button_width = 100
        button_height = 25
        button_spacing = 10
        
        # Add button
        self.add_button = create_button(
            "Add",
            NSMakeRect(x, y, button_width, button_height),
            action=self.addPrompt_,
            target=self
        )
        self.view.addSubview_(self.add_button)
        
        x += button_width + button_spacing
        
        # Edit button
        self.edit_button = create_button(
            "Edit",
            NSMakeRect(x, y, button_width, button_height),
            action=self.editPrompt_,
            target=self
        )
        self.edit_button.setEnabled_(False)
        self.view.addSubview_(self.edit_button)
        
        x += button_width + button_spacing
        
        # Duplicate button
        self.duplicate_button = create_button(
            "Duplicate",
            NSMakeRect(x, y, button_width, button_height),
            action=self.duplicatePrompt_,
            target=self
        )
        self.duplicate_button.setEnabled_(False)
        self.view.addSubview_(self.duplicate_button)
        
        x += button_width + button_spacing
        
        # Delete button
        self.delete_button = create_button(
            "Delete",
            NSMakeRect(x, y, button_width, button_height),
            action=self.deletePrompt_,
            target=self
        )
        self.delete_button.setEnabled_(False)
        self.view.addSubview_(self.delete_button)
        
    def _load_prompts(self):
        """Load prompts from settings"""
        try:
            prompts = self.settings_manager.get("prompts", [])
            logger.debug(f"Loaded {len(prompts)} prompts for table view")
            
            # Log prompt details for debugging
            for i, prompt in enumerate(prompts):
                name = prompt.get('name', '')
                text_len = len(prompt.get('text', ''))
                logger.debug(f"Loaded prompt {i+1}: name='{name}', text_length={text_len}")
            
            self.data_source.set_prompts(prompts)
            self.table_view.reloadData()
            
            logger.debug("Prompts table reloaded with data")
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            self.data_source.set_prompts([])
            self.table_view.reloadData()
            
    def _save_prompts(self):
        """Save prompts to settings"""
        try:
            self.settings_manager.set_setting("prompts", self.data_source.prompts)
            self._notify_settings_changed()
            logger.info(f"Saved {len(self.data_source.prompts)} prompts")
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
            
    # Action methods
    def addPrompt_(self, sender):
        """Add a new prompt"""
        logger.debug("Adding new prompt")
        
        dialog = PromptDialog.alloc().init()
        dialog.setValidator_(self.validator)
        dialog.setExistingPromptNames_([p["name"] for p in self.data_source.prompts])
        
        if dialog.showModal() == 1:  # OK clicked
            name = dialog.getName()
            text = dialog.getText()
            
            # Add new prompt
            new_prompt = {"name": name, "text": text}
            self.data_source.prompts.append(new_prompt)
            
            # Save and reload
            self._save_prompts()
            self.table_view.reloadData()
            
            # Select new row
            new_row = len(self.data_source.prompts) - 1
            self.table_view.selectRowIndexes_byExtendingSelection_(
                NSIndexSet.indexSetWithIndex_(new_row), False
            )
            
            # Animate addition
            self.table_view.beginUpdates()
            self.table_view.insertRowsAtIndexes_withAnimation_(
                NSIndexSet.indexSetWithIndex_(new_row),
                NSTableViewAnimationSlideDown
            )
            self.table_view.endUpdates()
            
            logger.info(f"Added new prompt: {name}")
            
    def editPrompt_(self, sender):
        """Edit selected prompt"""
        row = self.table_view.selectedRow()
        if row < 0:
            return
            
        prompt = self.data_source.prompts[row]
        logger.debug(f"Editing prompt: {prompt['name']}")
        
        dialog = PromptDialog.alloc().init()
        dialog.setValidator_(self.validator)
        dialog.setExistingPromptNames_(
            [p["name"] for i, p in enumerate(self.data_source.prompts) if i != row]
        )
        dialog.setName_(prompt["name"])
        dialog.setText_(prompt["text"])
        dialog.setEditMode_(True)
        
        if dialog.showModal() == 1:  # OK clicked
            # Update prompt
            self.data_source.prompts[row] = {
                "name": dialog.getName(),
                "text": dialog.getText()
            }
            
            # Save and reload
            self._save_prompts()
            self.table_view.reloadData()
            
            logger.info(f"Updated prompt: {dialog.getName()}")
            
    def duplicatePrompt_(self, sender):
        """Duplicate selected prompt"""
        row = self.table_view.selectedRow()
        if row < 0:
            return
            
        prompt = self.data_source.prompts[row]
        logger.debug(f"Duplicating prompt: {prompt['name']}")
        
        # Generate unique name
        base_name = prompt["name"]
        copy_name = f"{base_name} Copy"
        counter = 1
        
        existing_names = [p["name"] for p in self.data_source.prompts]
        while copy_name in existing_names:
            counter += 1
            copy_name = f"{base_name} Copy {counter}"
            
        # Create duplicate
        new_prompt = {
            "name": copy_name,
            "text": prompt["text"]
        }
        self.data_source.prompts.append(new_prompt)
        
        # Save and reload
        self._save_prompts()
        self.table_view.reloadData()
        
        # Select new row
        new_row = len(self.data_source.prompts) - 1
        self.table_view.selectRowIndexes_byExtendingSelection_(
            NSIndexSet.indexSetWithIndex_(new_row), False
        )
        
        logger.info(f"Duplicated prompt as: {copy_name}")
        
    def deletePrompt_(self, sender):
        """Delete selected prompt with confirmation dialog"""
        row = self.table_view.selectedRow()
        if row < 0:
            return
            
        prompt = self.data_source.prompts[row]
        logger.debug(f"Deleting prompt: {prompt['name']}")
        
        # Show confirmation dialog with themed icon
        from AppKit import NSAlert, NSAlertFirstButtonReturn
        
        alert = NSAlert.alloc().init()
        alert.setMessageText_(f"Delete prompt '{prompt['name']}'?")
        alert.setInformativeText_("This action cannot be undone.")
        alert.addButtonWithTitle_("Delete")
        alert.addButtonWithTitle_("Cancel")
        alert.setAlertStyle_(2)  # NSAlertStyleCritical
        
        # Set themed icon - get parent window to access _set_dialog_icon method
        parent_window = self.view.window()
        if parent_window and hasattr(parent_window.windowController(), '_set_dialog_icon'):
            parent_window.windowController()._set_dialog_icon(alert)
        
        # Show modal dialog
        response = alert.runModal()
        
        if response == NSAlertFirstButtonReturn:  # Delete button clicked
            # Animate removal
            self.table_view.beginUpdates()
            self.table_view.removeRowsAtIndexes_withAnimation_(
                NSIndexSet.indexSetWithIndex_(row),
                NSTableViewAnimationSlideUp
            )
            self.table_view.endUpdates()
            
            # Remove from data
            self.data_source.prompts.pop(row)
            
            # Save
            self._save_prompts()
            
            logger.info(f"Deleted prompt: {prompt['name']}")
        else:
            logger.debug("Delete prompt cancelled by user")
        
    # Table view delegate methods
    def tableViewSelectionDidChange_(self, notification):
        """Handle table selection changes"""
        row = self.table_view.selectedRow()
        has_selection = row >= 0
        
        self.edit_button.setEnabled_(has_selection)
        self.duplicate_button.setEnabled_(has_selection)
        self.delete_button.setEnabled_(has_selection)
        
    def tableView_shouldEditTableColumn_row_(self, table_view, column, row):
        """Prevent inline editing"""
        return False
        
    def _notify_settings_changed(self):
        """Notify that settings have changed"""
        if self.on_settings_changed:
            try:
                self.on_settings_changed()
            except Exception as e:
                logger.error(f"Error in settings changed callback: {e}") 