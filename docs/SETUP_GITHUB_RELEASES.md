# GitHub Releases Setup Guide

You're almost ready to use the new GitHub releases distribution system! Just a few more steps to complete the setup.

## ✅ Completed
- [x] GitHub CLI installed (`gh`)
- [x] Release scripts created
- [x] Pre-commit hook updated
- [x] Documentation updated

## 🔧 Final Setup Steps

### 1. Authenticate GitHub CLI
Run this command and follow the prompts:
```bash
gh auth login
```

**Choose these options:**
- **Host**: GitHub.com
- **Protocol**: HTTPS (recommended) or SSH
- **Authentication**: 
  - Option A: Login with web browser (easiest)
  - Option B: Paste an authentication token

### 2. Verify Authentication
```bash
gh auth status
```
You should see: `✓ Logged in to github.com as YOUR_USERNAME`

### 3. Test the System
```bash
# Option A: Test manual release creation
./scripts/manual_release.sh

# Option B: Test via pre-commit hook
git add SETUP_GITHUB_RELEASES.md
git commit -m "Set up GitHub releases system"
# Hook will ask if you want to create a release
```

## 🚀 Using the New System

### Creating Releases

#### Automatic (Recommended)
1. Make changes to Python files
2. Commit to main/master branch
3. Pre-commit hook will ask if you want to create a release

#### Manual
```bash
./scripts/manual_release.sh
```

### What Happens During Release
1. **Builds app** with PyInstaller
2. **Creates archives** (ZIP + TAR.GZ)
3. **Generates release notes** automatically
4. **Uploads to GitHub** as a new release
5. **Creates installation instructions**

### Version Management
- First release: Script will ask for version (e.g., `v1.0.0`)
- Subsequent releases: Uses git tags automatically
- Manual tagging: `git tag v1.0.1 && git push origin v1.0.1`

## 📦 Distribution Benefits

### For You (Developer)
- ✅ Centralized release management
- ✅ Automatic version tracking
- ✅ Professional release notes
- ✅ Download analytics
- ✅ Easy rollback to previous versions

### For Users
- ✅ Official download location
- ✅ Always latest version available
- ✅ Installation instructions included
- ✅ Multiple download formats
- ✅ Verified app bundles

## 🔄 Migration from Old System

If you had the old local distribution system:

```bash
# Clean old files
rm -rf distribution/

# The new system will recreate this folder during releases
```

## 📝 Release Workflow Example

```bash
# 1. Make changes
echo "console.log('New feature');" >> some_file.py

# 2. Commit (this triggers the release workflow)
git add .
git commit -m "Add awesome new feature"

# 3. Pre-commit hook asks: "Create a GitHub release? (y/N)"
# Type 'y' and press Enter

# 4. Follow prompts for version and release notes

# 5. Release is automatically created on GitHub! 🎉
```

## 🛠 Troubleshooting

### "GitHub CLI not found"
```bash
brew install gh
```

### "Not authenticated"
```bash
gh auth login
```

### "Release already exists"
The script will offer to delete and recreate it.

### Build fails
```bash
# Check virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Try manual release
./scripts/manual_release.sh
```

## 📚 Documentation

- **Full Documentation**: See `DISTRIBUTION.md`
- **Scripts**: Check `scripts/` folder
- **Pre-commit Hook**: `.githooks/pre-commit`

## 🎯 Next Steps

1. **Complete authentication** (`gh auth login`)
2. **Test release creation** (`./scripts/manual_release.sh`)
3. **Create your first release**!
4. **Share the GitHub releases link** with users

Once set up, you'll have a professional distribution system that automatically handles:
- App building
- Version management
- Release notes
- File hosting
- User downloads

Your users will be able to download Potter directly from your GitHub Releases page! 🚀 