#!/usr/bin/env python3
"""
Potter Release Manager with Auto-Update Support
Refactored with utility classes for better organization and error handling
"""

import os
import sys
import subprocess
import json
import argparse
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import re
from typing import Optional, Dict, Any

# Import our utilities
from version_manager import get_current_version, set_version, bump_version
from release_utils import generate_ai_release_notes, get_commits_for_release_notes


class ReleaseConfig:
    """Configuration for release process"""
    
    def __init__(self):
        self.repo_name = "graydot/potter"
        self.github_repo_url = f"https://github.com/{self.repo_name}"
        self.releases_dir = "releases"
        self.app_name = "Potter"
        self.sparkle_tool = "swift-potter/.build/artifacts/sparkle/Sparkle/bin/generate_appcast"


class CodenameManager:
    """Handles codename operations"""
    
    @staticmethod
    def get_current_codename() -> str:
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from codename_utils import get_current_codename
            return get_current_codename()
        except Exception as e:
            print(f"⚠️  Could not get codename: {e}")
            return "Unknown"
    
    @staticmethod
    def get_enhanced_release_title(version: str) -> str:
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from codename_utils import get_enhanced_release_title
            return get_enhanced_release_title(version)
        except Exception as e:
            print(f"⚠️  Could not get codename for release title: {e}")
            return f"Potter {version}"
    
    @staticmethod
    def get_enhanced_dmg_name(version: str) -> str:
        try:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from codename_utils import get_enhanced_dmg_name
            return get_enhanced_dmg_name(version)
        except Exception as e:
            return f"Potter-{version}.dmg"


class ReleaseNotesManager:
    """Handles release notes generation and input"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.codename_manager = CodenameManager()
    
    def get_release_notes(self, version: str, use_ai: bool = True) -> str:
        """Get release notes using AI generation or manual input"""
        codename = self.codename_manager.get_current_codename()
        print(f"\n🎭 This release codename: {codename}")
        
        if use_ai:
            ai_notes = self._try_ai_generation(version, codename)
            if ai_notes:
                return ai_notes
        
        return self._get_manual_notes(version, codename)
    
    def _try_ai_generation(self, version: str, codename: str) -> Optional[str]:
        """Try to generate AI release notes"""
        print(f"\n🤖 Attempting to generate AI release notes...")
        ai_notes = generate_ai_release_notes(version, codename)
        
        if not ai_notes:
            print("❌ AI generation failed, falling back to manual entry...")
            return None
        
        print("\n📝 AI-generated release notes:")
        print("=" * 60)
        print(ai_notes)
        print("=" * 60)
        
        try:
            response = input("\nUse these AI-generated notes? [Y/n]: ").strip().lower()
            if response in ['', 'y', 'yes']:
                return ai_notes
            elif response in ['e', 'edit']:
                return self._edit_ai_notes(ai_notes)
            else:
                print("📝 Falling back to manual notes entry...")
                return None
        except (EOFError, KeyboardInterrupt):
            print("\n📝 Using AI-generated notes...")
            return ai_notes
    
    def _edit_ai_notes(self, ai_notes: str) -> str:
        """Allow editing of AI-generated notes"""
        print("\n📝 Edit the AI-generated notes (press Ctrl+D when done):")
        lines = ai_notes.split('\n')
        
        for i, line in enumerate(lines):
            try:
                new_line = input(f"{i+1:2d}: {line}\n    ")
                if new_line.strip():
                    lines[i] = new_line
            except EOFError:
                break
        
        return '\n'.join(lines)
    
    def _get_manual_notes(self, version: str, codename: str) -> str:
        """Get manual release notes input"""
        print(f"\n📝 Enter release notes for '{codename}' (press Ctrl+D when done):")
        print("=" * 60)
        print(f"💡 Tip: Consider theming your notes around '{codename}' for consistency!")
        print(f"💡 Or type 'ai' on a new line to retry AI generation")
        print("=" * 60)
        
        lines = []
        try:
            while True:
                line = input()
                if line.strip().lower() == 'ai':
                    print("🤖 Retrying AI generation...")
                    ai_notes = generate_ai_release_notes(version, codename)
                    if ai_notes:
                        return ai_notes
                    else:
                        print("❌ AI generation failed again, continue with manual entry...")
                        continue
                lines.append(line)
        except EOFError:
            pass
        
        user_notes = "\n".join(lines).strip()
        
        if user_notes:
            return self._enhance_manual_notes(user_notes, codename)
        else:
            return self._get_default_notes(codename)
    
    def _enhance_manual_notes(self, user_notes: str, codename: str) -> str:
        """Enhance manual notes with codename context"""
        enhanced_notes = f"## 🎭 {codename}\n\n{user_notes}"
        if codename.lower() not in user_notes.lower():
            enhanced_notes += f"\n\n*This release is codenamed **{codename}** - bringing AI-powered text processing with creative flair to macOS.*"
        return enhanced_notes
    
    def _get_default_notes(self, codename: str) -> str:
        """Get default template notes"""
        return f"""## 🎭 {codename}

*{codename}* brings enhanced AI-powered text processing to macOS with improved performance and reliability.

### What's New
- Performance improvements and bug fixes
- Enhanced LLM integration
- Better error handling and user experience

*This release is codenamed **{codename}** - continuing Potter's tradition of elegant, powerful text processing.*"""


class AppBuilder:
    """Handles app building operations"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
    
    def build_app(self) -> bool:
        """Build the app using the build script with proper signing"""
        print("🔨 Building signed Potter.app for release...")
        
        try:
            result = subprocess.run(['make', 'build'], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Signed build completed successfully")
                return True
            else:
                print(f"❌ Build failed with return code {result.returncode}")
                if result.stdout:
                    print(f"STDOUT: {result.stdout}")
                if result.stderr:
                    print(f"STDERR: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False


class AppcastManager:
    """Handles appcast generation and updates"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
    
    def calculate_file_signature(self, file_path: str) -> str:
        """Calculate EdDSA signature using Sparkle's generate_appcast tool"""
        if not os.path.exists(self.config.sparkle_tool):
            raise FileNotFoundError(f"❌ Sparkle generate_appcast tool not found at {self.config.sparkle_tool}")
        
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy DMG to temp directory with version in filename
            import shutil
            
            original_name = Path(file_path).stem
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', original_name)
            if not version_match:
                raise ValueError(f"❌ Could not extract version from DMG filename: {original_name}")
            
            version_str = version_match.group(1)
            temp_dmg = os.path.join(temp_dir, f"Potter-{version_str}.dmg")
            shutil.copy2(file_path, temp_dmg)
            
            # Run generate_appcast
            result = subprocess.run([self.config.sparkle_tool, temp_dir], 
                                   capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = f"❌ generate_appcast failed with exit code {result.returncode}"
                if result.stdout:
                    error_msg += f"\nSTDOUT: {result.stdout}"
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr}"
                raise subprocess.CalledProcessError(result.returncode, [self.config.sparkle_tool, temp_dir], error_msg)
            
            # Parse generated appcast to extract signature
            temp_appcast = os.path.join(temp_dir, "appcast.xml")
            if not os.path.exists(temp_appcast):
                raise FileNotFoundError(f"❌ generate_appcast did not create appcast.xml in {temp_dir}")
                
            tree = ET.parse(temp_appcast)
            root = tree.getroot()
            
            for enclosure in root.findall(".//enclosure"):
                ed_sig = enclosure.get("{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature")
                if ed_sig:
                    print(f"✅ Generated EdDSA signature: {ed_sig[:20]}...")
                    return ed_sig
            
            raise ValueError("❌ No EdDSA signature found in generated appcast")
    
    def update_appcast(self, version: str, dmg_path: str, release_notes: str, dmg_name: str) -> str:
        """Update or create appcast.xml file"""
        print("📡 Updating appcast.xml...")
        
        os.makedirs(self.config.releases_dir, exist_ok=True)
        appcast_path = f"{self.config.releases_dir}/appcast.xml"
        
        download_url = f"{self.config.github_repo_url}/releases/download/v{version}/{dmg_name}"
        print(f"🎭 Using DMG filename for download URL: {dmg_name}")
        
        # Create appcast entry
        file_size = os.path.getsize(dmg_path)
        signature = self.calculate_file_signature(dmg_path)
        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        
        # Load existing appcast or create new one
        if os.path.exists(appcast_path):
            tree = ET.parse(appcast_path)
            root = tree.getroot()
            channel = root.find('channel')
        else:
            root = ET.Element('rss', version='2.0', attrib={
                'xmlns:sparkle': 'http://www.andymatuschak.org/xml-namespaces/sparkle',
                'xmlns:dc': 'http://purl.org/dc/elements/1.1/'
            })
            
            channel = ET.SubElement(root, 'channel')
            ET.SubElement(channel, 'title').text = f"{self.config.app_name} Updates"
            ET.SubElement(channel, 'description').text = f"Updates for {self.config.app_name}"
            ET.SubElement(channel, 'language').text = "en"
            ET.SubElement(channel, 'link').text = self.config.github_repo_url
            
            tree = ET.ElementTree(root)
        
        # Add new item
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = f"{self.config.app_name} {version}"
        ET.SubElement(item, 'description').text = f"<![CDATA[{release_notes}]]>"
        ET.SubElement(item, 'pubDate').text = pub_date
        
        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', download_url)
        enclosure.set('length', str(file_size))
        enclosure.set('type', 'application/octet-stream')
        enclosure.set('{http://www.andymatuschak.org/xml-namespaces/sparkle}version', version)
        enclosure.set('{http://www.andymatuschak.org/xml-namespaces/sparkle}shortVersionString', version)
        enclosure.set('{http://www.andymatuschak.org/xml-namespaces/sparkle}edSignature', signature)
        
        # Write appcast
        ET.indent(tree, space="  ", level=0)
        tree.write(appcast_path, encoding='utf-8', xml_declaration=True)
        
        print(f"✅ Updated appcast: {appcast_path}")
        return appcast_path


class GitManager:
    """Handles git operations"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
    
    def commit_appcast_changes(self, version: str) -> bool:
        """Commit appcast changes"""
        print("📡 Committing appcast changes...")
        
        try:
            subprocess.run(['git', 'add', 'releases/appcast.xml'], check=True)
            commit_msg = f"Update appcast for Potter {version}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            print(f"✅ Appcast changes committed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            return False
    
    def commit_version_changes(self, version: str) -> bool:
        """Commit version changes to git"""
        print("📝 Committing version changes...")
        
        try:
            subprocess.run(['git', 'add', 
                           'scripts/build_app.py',
                           'swift-potter/Sources/Resources/Info.plist'],
                          check=True)
            
            commit_message = f"Release {version}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            print("✅ Version changes committed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Git commit failed: {e}")
            return False
    
    def prompt_git_push(self) -> bool:
        """Prompt user to push commits to remote"""
        print("\n" + "=" * 60)
        print("🚀 PUSH TO REMOTE REPOSITORIES")
        print("=" * 60)
        print("This will push commits on master to remote")
        print()
        
        try:
            response = input("Push commits to remote? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                print("📤 Pushing commits to remote...")
                
                try:
                    subprocess.run(['git', 'push'], check=True)
                    subprocess.run(['git', 'push', '--tags'], check=True)
                    print("✅ Commits pushed successfully")
                    return True
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to push: {e}")
                    return False
            else:
                print("⏭️  Skipping push to remote (user chose N)")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\n⏭️  Skipping push to remote (interrupted)")
            return False


class GitHubManager:
    """Handles GitHub release operations"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.codename_manager = CodenameManager()
    
    def create_github_release(self, version: str, dmg_path: str, release_notes: str) -> bool:
        """Create GitHub release using gh CLI"""
        print(f"🚀 Creating GitHub release v{version}...")
        
        try:
            subprocess.run(['gh', '--version'], capture_output=True, check=True)
            
            release_title = self.codename_manager.get_enhanced_release_title(version)
            print(f"🎭 Using enhanced release title: {release_title}")
            
            dmg_absolute_path = os.path.abspath(dmg_path)
            
            # Create tag first
            print(f"🏷️  Creating tag v{version}...")
            subprocess.run(['git', 'tag', f'v{version}'], check=False)
            subprocess.run(['git', 'push', 'origin', f'v{version}'], check=False)
            
            # Create release
            cmd = [
                'gh', 'release', 'create', f'v{version}',
                dmg_absolute_path,
                '--title', release_title,
                '--notes', release_notes
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ GitHub release created: {self.config.github_repo_url}/releases/tag/v{version}")
                return True
            else:
                stderr = result.stderr.strip()
                if "already exists" in stderr:
                    print(f"⚠️  GitHub release v{version} already exists - skipping creation")
                    print(f"🔗 Existing release: {self.config.github_repo_url}/releases/tag/v{version}")
                    return True
                else:
                    print(f"❌ GitHub release failed: {stderr}")
                    return False
                    
        except subprocess.CalledProcessError:
            print("❌ GitHub CLI (gh) not found. Please install it to create releases automatically.")
            print(f"💡 Manual steps:")
            print(f"   1. Go to {self.config.github_repo_url}/releases/new")
            print(f"   2. Tag: v{version}")
            print(f"   3. Upload: {dmg_path}")
            print(f"   4. Release notes: {release_notes}")
            return False
        except Exception as e:
            print(f"❌ GitHub release error: {e}")
            return False


class WebsiteUpdater:
    """Handles Potter webpage updates"""
    
    def __init__(self, config: ReleaseConfig):
        self.config = config
        self.codename_manager = CodenameManager()
    
    def update_potter_webpage(self, version: str) -> bool:
        """Update the Potter webpage download link"""
        print("\n📱 Updating Potter webpage...")
        
        webpage_path = os.path.expanduser("~/Workspace/graydot.github.io/products/potter.html")
        blog_repo_path = os.path.expanduser("~/Workspace/graydot.github.io")
        
        if not os.path.exists(webpage_path):
            print(f"⚠️  Potter webpage not found at {webpage_path}")
            return False
        
        if not os.path.exists(blog_repo_path):
            print(f"⚠️  Blog repo not found at {blog_repo_path}")
            return False
        
        try:
            with open(webpage_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dmg_name = self.codename_manager.get_enhanced_dmg_name(version)
            download_url = f"https://github.com/graydot/potter/releases/latest/download/{dmg_name}"
            
            # Update download link patterns
            pattern1 = r'(<a[^>]*href=")[^"]*("[^>]*id="potter-download-link")'
            pattern2 = r'(<a[^>]*id="potter-download-link"[^>]*href=")[^"]*(")'
            
            updated_content = re.sub(pattern1, f'\\1{download_url}\\2', content)
            if updated_content == content:
                updated_content = re.sub(pattern2, f'\\1{download_url}\\2', content)
            
            if updated_content == content:
                print("⚠️  No potter-download-link found to update")
                return False
            
            with open(webpage_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ Updated Potter webpage download link to {dmg_name}")
            
            # Commit and push blog repo
            return self._commit_blog_changes(blog_repo_path, version)
            
        except Exception as e:
            print(f"❌ Failed to update Potter webpage: {e}")
            return False
    
    def _commit_blog_changes(self, blog_repo_path: str, version: str) -> bool:
        """Commit and push blog repo changes"""
        try:
            original_cwd = os.getcwd()
            os.chdir(blog_repo_path)
            
            subprocess.run(['git', 'add', 'products/potter.html'], check=True)
            commit_msg = f"Update Potter download link to v{version}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            subprocess.run(['git', 'push'], check=True)
            
            print("✅ Potter webpage changes pushed to blog repo")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to commit/push blog changes: {e}")
            return False
        finally:
            os.chdir(original_cwd)


class ReleaseManager:
    """Main release manager orchestrating the entire process"""
    
    def __init__(self):
        self.config = ReleaseConfig()
        self.notes_manager = ReleaseNotesManager(self.config)
        self.app_builder = AppBuilder(self.config)
        self.appcast_manager = AppcastManager(self.config)
        self.git_manager = GitManager(self.config)
        self.github_manager = GitHubManager(self.config)
        self.website_updater = WebsiteUpdater(self.config)
        self.codename_manager = CodenameManager()
    
    def run_release(self, args) -> bool:
        """Run the complete release process"""
        try:
            # Get version information
            current_version = get_current_version()
            new_version = self._determine_new_version(args, current_version)
            
            print(f"📋 Current version: {current_version}")
            print(f"🆕 New version: {new_version}")
            
            # Get release notes
            release_notes = self._get_release_notes(args, new_version)
            
            # Update version
            set_version(new_version)
            print(f"✅ Version updated to {new_version}")
            
            # Build and get DMG
            dmg_path, dmg_name = self._build_and_get_dmg(new_version)
            
            # Update appcast
            appcast_path = self.appcast_manager.update_appcast(new_version, dmg_path, release_notes, dmg_name)
            
            # Commit changes
            self.git_manager.commit_appcast_changes(new_version)
            
            # Create GitHub release
            self.github_manager.create_github_release(new_version, dmg_path, release_notes)
            
            # Commit version changes
            self.git_manager.commit_version_changes(new_version)
            
            # Prompt to push
            if not self.git_manager.prompt_git_push():
                self._handle_no_push(new_version)
                return False
            
            # Update website
            self.website_updater.update_potter_webpage(new_version)
            
            self._print_success_summary(new_version, dmg_path, appcast_path)
            return True
            
        except Exception as e:
            print(f"❌ Release failed: {e}")
            return False
    
    def _determine_new_version(self, args, current_version: str) -> str:
        """Determine the new version number"""
        if args.version:
            if not re.match(r'^\d+\.\d+\.\d+$', args.version):
                raise ValueError(f"Invalid version format: {args.version}. Must be X.Y.Z")
            return args.version
        
        suggested_version = bump_version(current_version, args.bump)
        print(f"💡 Suggested version ({args.bump} bump): {suggested_version}")
        
        try:
            user_input = input(f"Enter version (press Enter for {suggested_version}): ").strip()
            if user_input:
                if not re.match(r'^\d+\.\d+\.\d+$', user_input):
                    raise ValueError(f"Invalid version format: {user_input}. Must be X.Y.Z")
                return user_input
            else:
                return suggested_version
        except EOFError:
            print(f"Non-interactive mode: using {suggested_version}")
            return suggested_version
    
    def _get_release_notes(self, args, version: str) -> str:
        """Get release notes"""
        use_ai = not args.no_ai
        release_notes = self.notes_manager.get_release_notes(version, use_ai)
        
        if not release_notes:
            raise ValueError("Release notes are required")
        
        return release_notes
    
    def _build_and_get_dmg(self, version: str) -> tuple:
        """Build app and return DMG path and name"""
        expected_dmg_name = self.codename_manager.get_enhanced_dmg_name(version)
        expected_dmg_path = f"dist/{expected_dmg_name}"
        
        if not self.app_builder.build_app():
            raise RuntimeError("Build failed")
        
        import time
        time.sleep(3)  # Wait for DMG to be ready
        
        if not os.path.exists(expected_dmg_path):
            raise RuntimeError(f"Expected DMG not found: {expected_dmg_path}")
        
        return expected_dmg_path, expected_dmg_name
    
    def _handle_no_push(self, version: str):
        """Handle case where user chose not to push"""
        print("\n❌ Release process aborted!")
        print("=" * 50)
        print("🚨 Release was not completed because changes were not pushed to remote.")
        print("📋 To complete the release manually:")
        print("1. Push Potter repo: git push && git push --tags")
        print("2. Push blog repo changes (if any)")
        print("3. Verify the GitHub release was created")
        print("4. Update Potter webpage download link manually")
    
    def _print_success_summary(self, version: str, dmg_path: str, appcast_path: str):
        """Print success summary"""
        print("\n🎉 Release process completed!")
        print("=" * 50)
        print(f"📋 Version: {version}")
        print(f"📦 DMG: {dmg_path}")
        print(f"📡 Appcast: {appcast_path}")
        print(f"🔗 Releases: {self.config.github_repo_url}/releases")
        print()
        print("📋 Next steps:")
        print("1. Test the DMG installation")
        print("2. ✅ Repositories pushed to remote")
        print("3. ✅ Potter webpage updated with new download link")
        print("4. Verify auto-update works with new appcast")


def main():
    parser = argparse.ArgumentParser(description='Potter Release Manager')
    parser.add_argument('--bump', choices=['major', 'minor', 'patch'], 
                       default='patch', help='Version bump type')
    parser.add_argument('--version', help='Specific version to release')
    parser.add_argument('--no-ai', action='store_true',
                       help='Skip AI-generated release notes')
    
    args = parser.parse_args()
    
    print("🎭 Potter Release Manager")
    print("=" * 50)
    
    release_manager = ReleaseManager()
    success = release_manager.run_release(args)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()