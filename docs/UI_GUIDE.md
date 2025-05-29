# 🎛️ Rephrasely Settings UI Guide

**Complete guide to customizing your Rephrasely experience**

## 🚀 Quick Start

### Opening the Settings
1. **Launch Rephrasely.app** from Applications
2. **Right-click** the blue "R" icon in your menu bar
3. **Select "Preferences..."**

Or use the keyboard shortcut: `Cmd+,` (while Rephrasely is focused)

## 📝 Prompts Tab - Customize Your AI

### What You Can Do
- **Edit any processing mode prompt** to fit your specific needs
- **Add context and instructions** for better AI results
- **Reset to defaults** if you want to start over
- **Preview changes** in real-time

### Example Customizations

#### Professional Writing
```
Rephrase: "Rewrite this text for a professional business audience, ensuring clarity and executive-level communication:"

Summarize: "Create an executive summary with key points and actionable insights:"

Expand: "Develop this into a comprehensive analysis with supporting details and recommendations:"
```

#### Creative Content
```
Rephrase: "Transform this into engaging, creative content that captures attention:"

Casual: "Rewrite this with personality, humor, and conversational tone:"

Formal: "Convert this to sophisticated, literary prose:"
```

#### Technical Documentation
```
Rephrase: "Rewrite this as clear, precise technical documentation with proper terminology:"

Expand: "Develop this into comprehensive technical documentation with examples and implementation details:"

Summarize: "Create a concise technical overview with key specifications:"
```

### Advanced Prompt Techniques

#### Context Setting
```
"You are writing for [audience]. Please [action] this text to [goal]:"

Examples:
- "You are writing for software developers. Please rephrase this text to be more technically precise:"
- "You are writing for marketing executives. Please expand this text to highlight business value:"
```

#### Output Formatting
```
"Please rewrite this text as [format]:"

Examples:
- "Please rewrite this text as bullet points with clear action items:"
- "Please rewrite this text as a professional email with subject line:"
- "Please rewrite this text as social media posts with hashtags:"
```

#### Tone and Style
```
"Please rewrite this in a [tone] tone for [context]:"

Examples:
- "Please rewrite this in a persuasive tone for sales presentations:"
- "Please rewrite this in an empathetic tone for customer support:"
- "Please rewrite this in an authoritative tone for policy documents:"
```

## ⚡ General Tab - Core Settings

### Global Hotkey
- **Default**: `Cmd+Shift+R`
- **Popular alternatives**:
  - `Cmd+Alt+R` - Easy to reach
  - `Cmd+Shift+T` - Text transformation
  - `Ctrl+Shift+A` - Windows-style
  - `Cmd+Option+Space` - Spacebar trigger

### Auto-paste Setting
- **Enabled** (default): Automatically replaces selected text
- **Disabled**: Puts result in clipboard for manual pasting

### Notifications
- **Enabled** (default): Shows success/error messages
- **Disabled**: Silent operation

## 🤖 Advanced Tab - AI Configuration

### AI Model Selection

#### GPT-3.5-turbo
- ✅ **Best for**: Fast, everyday text processing
- ✅ **Speed**: Very fast (1-2 seconds)
- ✅ **Cost**: Most economical
- ⚠️ **Quality**: Good but basic

#### GPT-4
- ✅ **Best for**: High-quality, complex text transformation
- ✅ **Quality**: Excellent reasoning and nuance
- ⚠️ **Speed**: Slower (3-5 seconds)
- ⚠️ **Cost**: More expensive

#### GPT-4-turbo
- ✅ **Best for**: Latest features and capabilities
- ✅ **Speed**: Faster than GPT-4
- ✅ **Quality**: Best available
- ⚠️ **Cost**: Most expensive

### Token Settings

#### Max Tokens (100-4000)
- **Low (100-300)**: Quick edits, simple rephrasing
- **Medium (500-1000)**: Standard processing (default: 1000)
- **High (1500-4000)**: Long content, detailed expansions

#### Temperature (0.0-1.0)
- **Conservative (0.0-0.3)**: Consistent, predictable results
- **Balanced (0.4-0.7)**: Good mix of creativity and reliability (default: 0.7)
- **Creative (0.8-1.0)**: More varied, creative outputs

### Export/Import Settings

#### Exporting Settings
1. Click **"Export Settings"**
2. Choose save location
3. Settings saved as JSON file
4. Share with team or backup

#### Importing Settings
1. Click **"Import Settings"**
2. Select JSON settings file
3. Settings loaded immediately
4. Click "Apply" or "Save" to confirm

## 🎯 Workflow Examples

### Email Enhancement Workflow
1. **Draft email** in your email client
2. **Select entire email** (Cmd+A)
3. **Press hotkey** (Cmd+Shift+R)
4. **Choose "Formal" mode** for professional tone
5. **Review and send** enhanced email

### Documentation Workflow
1. **Write rough notes** in any text editor
2. **Select section** to improve
3. **Press hotkey** 
4. **Use "Expand" mode** for detailed documentation
5. **Repeat** for each section

### Social Media Workflow
1. **Write formal announcement**
2. **Select text**
3. **Press hotkey**
4. **Use "Casual" mode** for social media tone
5. **Copy result** to social platform

## 🎨 Custom Mode Creation

### Adding New Modes
While you can't add new modes through the UI yet, you can create specialized prompts:

#### Customer Support Mode
```
Rephrase: "Rewrite this as a helpful, empathetic customer support response with clear next steps:"
```

#### Sales Mode
```
Rephrase: "Transform this into persuasive sales copy that highlights benefits and creates urgency:"
```

#### Academic Mode
```
Rephrase: "Rewrite this in formal academic style with proper citations and scholarly tone:"
```

## 🔧 Advanced Configuration

### Settings File Location
Your settings are saved in: `~/Applications/Rephrasely.app/Contents/MacOS/settings.json`

### Manual Settings Editing
You can manually edit the JSON file for advanced configurations:

```json
{
  "prompts": {
    "rephrase": "Your custom prompt here",
    "email": "Convert this to a professional email:",
    "marketing": "Transform this into compelling marketing copy:",
    "support": "Rewrite as a helpful customer support response:"
  },
  "hotkey": "cmd+alt+r",
  "model": "gpt-4",
  "max_tokens": 1500,
  "temperature": 0.6,
  "auto_paste": true,
  "show_notifications": true
}
```

### Team Settings Sharing
1. **Export settings** from one machine
2. **Share JSON file** with team
3. **Import on other machines** for consistency
4. **Standardize prompts** across organization

## 🚨 Troubleshooting

### Settings Not Saving
- Check **file permissions** in app directory
- Try **"Apply"** before **"Save"**
- **Restart app** if needed

### UI Not Opening
- Ensure **PyObjC is available** for native macOS integration
- Check **Console.app** for error messages
- Try **restarting Rephrasely.app**

### Prompts Not Working
- **Test with simple prompts** first
- Check **AI model availability** in your OpenAI account
- Verify **API key** is valid and has credits

### Performance Issues
- **Lower max_tokens** for faster processing
- **Use GPT-3.5-turbo** for speed
- **Reduce temperature** for consistency

## 💡 Pro Tips

### Effective Prompt Writing
1. **Be specific** about desired output
2. **Include context** about audience
3. **Specify format** if needed
4. **Test and iterate** prompts

### Hotkey Selection
1. **Avoid conflicts** with existing shortcuts
2. **Choose memorable** combinations
3. **Consider hand position** for comfort
4. **Test in different apps**

### Model Selection Strategy
- **Development/Testing**: GPT-3.5-turbo
- **Important content**: GPT-4
- **High-volume usage**: GPT-3.5-turbo
- **Latest features**: GPT-4-turbo

## 🔄 Best Practices

### Prompt Maintenance
- **Review prompts** monthly
- **Update based on results**
- **Share effective prompts** with team
- **Keep backups** of working configurations

### Security
- **Don't share API keys** in settings exports
- **Use environment variables** for sensitive data
- **Review permissions** regularly

### Performance Optimization
- **Monitor token usage** for cost control
- **Optimize prompt length** for efficiency
- **Use appropriate model** for task complexity

---

**Master your Rephrasely settings and transform your text processing workflow! 🚀** 