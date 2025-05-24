# 📦 Rephrasely Distribution System

This document explains the automated distribution system for building and releasing the Rephrasely macOS app.

## 🏗️ Overview

The distribution system consists of:

1. **Build Script** (`scripts/build_for_distribution.sh`) - Creates the macOS app bundle
2. **Pre-commit Hook** (`.githooks/pre-commit`) - Automatically builds on main branch commits  
3. **GitHub Actions** (`.github/workflows/release.yml`) - Creates releases automatically
4. **Distribution Folder** (`distribution/`) - Contains ready-to-download app files

## 🚀 Quick Setup

1. **Install the git hooks:**
   ```bash
   ./scripts/setup_hooks.sh
   ```

2. **Test the build system:**
   ```bash
   ./scripts/build_for_distribution.sh
   ```

3. **Commit to main/master to trigger automatic build and release**

## 📋 How It Works

### 1. Pre-commit Hook Trigger

When you commit to `main` or `master` branch with changes to:
- `.py` files (Python source code)
- `requirements.txt` (dependencies)
- `build_app.py` (build configuration)
- `assets/` folder (app resources)

The pre-commit hook automatically:
1. Builds the app using PyInstaller
2. Creates a ZIP archive
3. Adds the distribution files to your commit

### 2. GitHub Actions Release

When distribution files are pushed to GitHub:
1. GitHub Actions detects changes in `distribution/`
2. Creates a new release with auto-generated version tag
3. Uploads the ZIP file as a release asset
4. Generates comprehensive release notes

### 3. Version Management

Versions are automatically generated using:
- Git tags (if available): `v1.2.3`
- Date + commit: `v2024.01.15-abc123f`

## 🔨 Build Process Details

The build script (`scripts/build_for_distribution.sh`) performs:

1. **Environment Setup**
   - Activates virtual environment
   - Installs/updates dependencies
   - Installs PyInstaller

2. **Version Detection**
   - Extracts version from git tags
   - Records build date and commit hash
   - Creates build info metadata

3. **App Building**
   - Uses PyInstaller with optimized settings
   - Includes all necessary hidden imports
   - Embeds app icon and metadata

4. **Bundle Configuration**
   - Updates Info.plist with version info
   - Sets LSUIElement for menu bar app
   - Adds privacy usage descriptions
   - Sets proper executable permissions

5. **Code Signing** (if available)
   - Detects Developer ID certificates
   - Signs the app bundle for distribution
   - Falls back gracefully if no certificate

6. **Packaging**
   - Copies to distribution folder
   - Creates ZIP archive for download
   - Generates size reports and metadata

## 📁 File Structure

```
distribution/
├── README.md              # User installation guide
├── BUILD_INFO.md          # Latest build information
├── Rephrasely.app/        # Complete macOS app bundle
└── Rephrasely.app.zip     # Compressed app for download

scripts/
├── build_for_distribution.sh  # Main build script
└── setup_hooks.sh             # Git hooks installer

.githooks/
└── pre-commit            # Pre-commit hook for auto-building

.github/workflows/
└── release.yml           # GitHub Actions for releases
```

## ⚙️ Configuration

### Customizing the Build

Edit `scripts/build_for_distribution.sh` to:
- Add additional PyInstaller options
- Include extra files or resources
- Modify code signing behavior
- Change app bundle configuration

### Pre-commit Hook Behavior

The hook only triggers when:
- Committing to `main` or `master` branch
- Changes include Python files or configuration
- All files pass pre-commit checks

To disable temporarily:
```bash
git commit --no-verify -m "Skip pre-commit hook"
```

### GitHub Actions

The workflow triggers on:
- Pushes to main/master with distribution changes
- Manual workflow dispatch from GitHub UI

## 🔧 Troubleshooting

### Build Fails
1. Check virtual environment is activated
2. Ensure all dependencies are installed
3. Verify PyInstaller is compatible with your Python version
4. Check for missing hidden imports

### Code Signing Issues
- Install Apple Developer certificates
- Or remove code signing section from build script
- Users will need to right-click → "Open" on first launch

### Pre-commit Hook Not Running
```bash
# Re-install hooks
./scripts/setup_hooks.sh

# Check hook is executable
ls -la .git/hooks/pre-commit

# Test manually
.git/hooks/pre-commit
```

### GitHub Actions Failing
- Check repository has write permissions for Actions
- Ensure GITHUB_TOKEN has release permissions
- Verify distribution files exist and are valid

## 📊 Release Management

### Manual Release
```bash
# Build locally
./scripts/build_for_distribution.sh

# Commit and push
git add distribution/
git commit -m "Update distribution build"
git push origin main
```

### Version Tags
```bash
# Create a version tag
git tag v1.2.3
git push origin v1.2.3

# This will be used for the next release
```

### Pre-release Testing
```bash
# Test build without committing
./scripts/build_for_distribution.sh

# Test the app manually
open distribution/Rephrasely.app
```

## 🎯 Best Practices

1. **Test Before Committing**
   - Always test the app locally before committing
   - Verify all features work in the built version

2. **Version Management**
   - Use semantic versioning for releases
   - Tag important versions explicitly

3. **Build Optimization**
   - Keep dependencies minimal
   - Regularly update PyInstaller
   - Test on different macOS versions

4. **User Experience**
   - Include clear installation instructions
   - Provide troubleshooting guidance
   - Maintain backward compatibility

## 🚦 Development Workflow

1. **Feature Development**
   ```bash
   git checkout -b feature/new-feature
   # ... develop and test ...
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

2. **Merge to Main** (triggers build)
   ```bash
   git checkout main
   git merge feature/new-feature
   git push origin main  # → Triggers build and release
   ```

3. **Release Published**
   - GitHub automatically creates release
   - Users can download from Releases page
   - Distribution folder updated with latest build

This system ensures every change to the main branch results in a tested, signed, and ready-to-distribute macOS application! 🎉 