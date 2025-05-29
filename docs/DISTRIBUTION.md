# Potter Distribution System

This document describes how Potter handles building and distributing releases via GitHub Releases.

## Overview

Potter now uses **GitHub Releases** for distribution instead of local build files. This provides:

- ✅ **Centralized Distribution**: All releases available on GitHub
- ✅ **Version Management**: Automatic tagging and release notes
- ✅ **Download Analytics**: Track download statistics
- ✅ **Release Notes**: Detailed changelog for each version
- ✅ **Multiple Formats**: ZIP and TAR.GZ for different preferences

## Quick Start

### For Users (Downloading)
1. Go to [GitHub Releases](https://github.com/YOUR_USERNAME/potter/releases)
2. Download `Potter.app.zip` from the latest release
3. Extract and drag to Applications folder
4. Follow installation instructions included in the release

### For Developers (Creating Releases)

#### Option 1: Automatic (via Pre-commit Hook)
```bash
# Make changes to Python files
git add .
git commit -m "Add new feature"  # Pre-commit hook will ask about creating release
```

#### Option 2: Manual Release
```bash
# Create a release manually anytime
./scripts/manual_release.sh
```

#### Option 3: Direct Script
```bash
# Use the release script directly
./scripts/create_github_release.sh
```

## Requirements

### For Release Creation
- **GitHub CLI**: `brew install gh`
- **Authentication**: `gh auth login`
- **Virtual Environment**: `.venv` with dependencies installed
- **Clean Git State**: No uncommitted changes

### For Users
- **macOS 10.14+**
- **OpenAI API Key**
- **Internet Connection**

## Release Process

### Automated (Pre-commit Hook)

The pre-commit hook will automatically:

1. **Detect Changes**: Check for Python, config, or documentation changes
2. **Ask Permission**: Prompt whether to create a release (for Python changes)
3. **Build App**: Use PyInstaller to create the macOS app bundle
4. **Create Archives**: Generate both ZIP and TAR.GZ formats
5. **Upload to GitHub**: Create release with files and auto-generated notes
6. **Generate Docs**: Include installation instructions with each release

### Manual Process

```bash
# 1. Ensure you're on main/master branch
git checkout main

# 2. Commit all changes
git add .
git commit -m "Prepare for release"

# 3. Create release
./scripts/manual_release.sh

# 4. Follow prompts for version and release notes
```

## File Structure

### Generated Files
```
distribution/
├── Potter.app/          # macOS app bundle
├── Potter.app.zip       # Compressed app (recommended)
├── Potter.app.tar.gz    # Alternative compression
└── INSTALLATION.md          # User installation guide
```

### Release Assets
Each GitHub release includes:
- `Potter.app.zip` (recommended download)
- `Potter.app.tar.gz` (alternative format)
- `INSTALLATION.md` (setup instructions)

## Version Management

### Automatic Versioning
- Uses Git tags for version numbers
- Format: `v1.0.0`, `v1.0.1`, `v2.0.0-beta`, etc.
- Follows semantic versioning

### Creating New Versions
```bash
# The release script will prompt for version if no tags exist
# Or manually create tags:
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Configuration

### App Bundle Settings
The build process automatically configures:
- **Bundle Identifier**: Set in Info.plist
- **Version Numbers**: From Git tags
- **Menu Bar App**: LSUIElement = true
- **Permission Descriptions**: For accessibility access
- **Code Signing**: Adhoc signature for distribution

### Release Notes
Auto-generated release notes include:
- Features and requirements
- Installation instructions
- Build information
- Download options
- Troubleshooting tips

## Troubleshooting

### Common Issues

#### "GitHub CLI not found"
```bash
brew install gh
gh auth login
```

#### "Not in a git repository"
Ensure you're in the project root directory.

#### "Uncommitted changes"
```bash
git add .
git commit -m "Prepare for release"
```

#### "Release already exists"
The script will offer to delete and recreate the release.

#### Build Failures
- Check virtual environment is activated
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check for Python syntax errors

### Manual Recovery

If automatic releases fail:

```bash
# 1. Clean build directories
rm -rf build/ dist/ distribution/

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run manual release
./scripts/manual_release.sh
```

## Migration from Old System

If you were using the old local distribution system:

1. **Remove old hooks**: The new pre-commit hook replaces the old one
2. **Install GitHub CLI**: `brew install gh && gh auth login`
3. **Clean old files**: `rm -rf distribution/` (will be regenerated)
4. **Test release**: Run `./scripts/manual_release.sh` to verify setup

## Best Practices

### For Release Creators
- ✅ Test the app locally before releasing
- ✅ Write descriptive commit messages
- ✅ Update documentation with new features
- ✅ Create releases from main/master branch only
- ✅ Include meaningful release notes

### For Users
- ✅ Download from official GitHub Releases only
- ✅ Verify file integrity (check file sizes)
- ✅ Read installation instructions for each release
- ✅ Report issues on the GitHub repository

## Scripts Reference

### `scripts/create_github_release.sh`
Main release creation script. Handles:
- Version management
- App building
- File compression
- GitHub release creation
- Release notes generation

### `scripts/manual_release.sh`
Simple wrapper for manual release creation.

### `.githooks/pre-commit`
Pre-commit hook that triggers releases for significant changes.

## Support

For distribution-related issues:
- Check this documentation
- Review GitHub Actions logs (if applicable)
- Create an issue on the GitHub repository
- Include build logs and error messages 