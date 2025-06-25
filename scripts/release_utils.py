#!/usr/bin/env python3
"""
Release utilities for Potter release management
Includes LLM-powered release notes generation and git utilities
"""

import os
import subprocess
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from dotenv import load_dotenv
import openai


class GitCommit:
    """Represents a git commit with metadata"""
    
    def __init__(self, hash: str, message: str, author: str, date: str, files_changed: List[str] = None):
        self.hash = hash
        self.message = message
        self.author = author
        self.date = date
        self.files_changed = files_changed or []
    
    def __str__(self):
        return f"{self.hash[:8]} - {self.message} ({self.author})"
    
    def to_dict(self):
        return {
            'hash': self.hash,
            'message': self.message,
            'author': self.author,
            'date': self.date,
            'files_changed': self.files_changed
        }


class GitAnalyzer:
    """Analyzes git repository for release information"""
    
    @staticmethod
    def get_last_release_tag() -> Optional[str]:
        """Get the last release tag (semantic version format)"""
        try:
            # Get all tags in reverse chronological order
            result = subprocess.run(['git', 'tag', '--sort=-version:refname'], 
                                  capture_output=True, text=True, check=True)
            
            # Filter for semantic version tags (v1.2.3 format)
            for tag in result.stdout.strip().split('\n'):
                if tag and re.match(r'^v?\d+\.\d+\.\d+$', tag):
                    return tag
            
            return None
        except subprocess.CalledProcessError:
            return None
    
    @staticmethod
    def get_commits_since_tag(tag: Optional[str] = None) -> List[GitCommit]:
        """Get commits since specified tag (or all commits if no tag)"""
        try:
            if tag:
                # Get commits since the tag
                cmd = ['git', 'log', f'{tag}..HEAD', '--pretty=format:%H|%s|%an|%ad', '--date=iso']
            else:
                # Get recent commits (last 50)
                cmd = ['git', 'log', '-50', '--pretty=format:%H|%s|%an|%ad', '--date=iso']
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        hash_val, message, author, date = parts
                        commit = GitCommit(hash_val, message, author, date)
                        
                        # Get files changed for this commit
                        files_result = subprocess.run(
                            ['git', 'show', '--name-only', '--pretty=format:', hash_val],
                            capture_output=True, text=True
                        )
                        if files_result.returncode == 0:
                            commit.files_changed = [f for f in files_result.stdout.strip().split('\n') if f]
                        
                        commits.append(commit)
            
            return commits
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to get commits: {e}")
            return []
    
    @staticmethod
    def get_repo_stats() -> Dict:
        """Get repository statistics"""
        try:
            # Get total commits
            total_commits_result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                capture_output=True, text=True, check=True
            )
            total_commits = int(total_commits_result.stdout.strip())
            
            # Get contributors
            contributors_result = subprocess.run(
                ['git', 'shortlog', '-sn', '--all'],
                capture_output=True, text=True, check=True
            )
            contributors = len(contributors_result.stdout.strip().split('\n'))
            
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True, check=True
            )
            current_branch = branch_result.stdout.strip()
            
            return {
                'total_commits': total_commits,
                'contributors': contributors,
                'current_branch': current_branch
            }
        except subprocess.CalledProcessError:
            return {}


class LLMReleaseNotesGenerator:
    """Generates release notes using OpenAI analysis of commits"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()
        
        if not self.api_key:
            raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in .env file or environment variable.")
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from .env file or environment variables"""
        # Load .env file from root directory
        env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(env_file_path)
        
        # Get OpenAI API key
        return os.getenv('OPENAI_API_KEY')
    
    def generate_release_notes(self, commits: List[GitCommit], version: str, 
                             codename: str = None, previous_version: str = None) -> str:
        """Generate release notes using LLM analysis of commits"""
        
        if not commits:
            return self._generate_fallback_notes(version, codename)
        
        # Prepare commit data for LLM
        commit_summary = self._prepare_commit_summary(commits)
        
        # Create prompt for LLM
        prompt = self._create_release_notes_prompt(commit_summary, version, codename, previous_version)
        
        # Call OpenAI
        try:
            return self._call_openai(prompt)
        except Exception as e:
            print(f"⚠️  OpenAI generation failed: {e}")
            print("📝 Falling back to manual release notes...")
            return self._generate_fallback_notes(version, codename)
    
    def _prepare_commit_summary(self, commits: List[GitCommit]) -> str:
        """Prepare a summary of commits for LLM analysis"""
        summary_lines = []
        
        for commit in commits:
            # Skip merge commits and release commits
            if (commit.message.startswith('Merge ') or 
                commit.message.startswith('Release ') or
                'release' in commit.message.lower() and len(commit.message.split()) <= 3):
                continue
            
            # Categorize commit types
            commit_type = self._categorize_commit(commit)
            files_info = f" (files: {', '.join(commit.files_changed[:3])}{'...' if len(commit.files_changed) > 3 else ''})" if commit.files_changed else ""
            
            summary_lines.append(f"- [{commit_type}] {commit.message}{files_info}")
        
        return '\n'.join(summary_lines)
    
    def _categorize_commit(self, commit: GitCommit) -> str:
        """Categorize commit type based on message and files"""
        message = commit.message.lower()
        
        # Check for conventional commit prefixes
        if message.startswith(('fix:', 'bug:')):
            return 'FIX'
        elif message.startswith(('feat:', 'feature:')):
            return 'FEATURE'
        elif message.startswith(('docs:', 'doc:')):
            return 'DOCS'
        elif message.startswith(('test:', 'tests:')):
            return 'TEST'
        elif message.startswith(('refactor:', 'style:')):
            return 'REFACTOR'
        elif message.startswith(('chore:', 'build:')):
            return 'CHORE'
        
        # Analyze by keywords
        if any(word in message for word in ['fix', 'bug', 'error', 'issue', 'crash']):
            return 'FIX'
        elif any(word in message for word in ['add', 'new', 'feature', 'implement', 'support']):
            return 'FEATURE'
        elif any(word in message for word in ['update', 'improve', 'enhance', 'better']):
            return 'IMPROVEMENT'
        elif any(word in message for word in ['remove', 'delete', 'clean']):
            return 'REMOVAL'
        elif any(word in message for word in ['test', 'spec']):
            return 'TEST'
        elif any(word in message for word in ['doc', 'readme', 'comment']):
            return 'DOCS'
        
        return 'MISC'
    
    def _create_release_notes_prompt(self, commit_summary: str, version: str, 
                                   codename: str = None, previous_version: str = None) -> str:
        """Create prompt for LLM to generate release notes"""
        
        codename_info = f" codenamed '{codename}'" if codename else ""
        prev_version_info = f" (previous version: {previous_version})" if previous_version else ""
        
        prompt = f"""
You are a technical writer creating release notes for Potter{codename_info}, a macOS AI-powered text processing application. 

Generate professional, user-friendly release notes for version {version}{prev_version_info} based on the following commit analysis:

{commit_summary}

Requirements:
1. Write in a clear, engaging tone suitable for end users
2. Group changes into logical categories (Features, Improvements, Bug Fixes, etc.)
3. Focus on user-visible changes and benefits
4. Use bullet points for easy scanning
5. Keep technical jargon to a minimum
6. If there's a codename, incorporate it creatively but professionally
7. Include a brief intro paragraph that highlights the main theme of this release
8. Don't mention internal refactoring unless it significantly impacts user experience

Format as markdown with proper headers and sections. Start with a brief release summary, then organize changes by category.
"""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API to generate release notes"""
        client = openai.OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a skilled technical writer specializing in software release notes."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_fallback_notes(self, version: str, codename: str = None) -> str:
        """Generate fallback release notes when LLM is unavailable"""
        codename_info = f" - {codename}" if codename else ""
        
        return f"""## Potter {version}{codename_info}

This release brings continued improvements to Potter's AI-powered text processing capabilities.

### What's New
- Performance improvements and optimizations
- Enhanced stability and reliability
- Bug fixes and user experience improvements

### Technical Updates
- Updated dependencies and security patches
- Code quality improvements
- Enhanced error handling

*Thank you for using Potter! Your feedback helps make each release better.*"""


def get_commits_for_release_notes(target_version: str = None) -> Tuple[List[GitCommit], Optional[str]]:
    """Get commits and last tag for release notes generation"""
    analyzer = GitAnalyzer()
    
    # Get last release tag
    last_tag = analyzer.get_last_release_tag()
    print(f"📋 Last release tag: {last_tag or 'None found'}")
    
    # Get commits since last tag
    commits = analyzer.get_commits_since_tag(last_tag)
    print(f"📋 Found {len(commits)} commits since last release")
    
    return commits, last_tag


def generate_ai_release_notes(version: str, codename: str = None, api_key: str = None) -> Optional[str]:
    """Generate AI-powered release notes for a version"""
    try:
        # Get commits for analysis
        commits, last_tag = get_commits_for_release_notes(version)
        
        if not commits:
            print("📝 No commits found since last release - using fallback notes")
            return None
        
        # Extract previous version from tag
        previous_version = None
        if last_tag:
            version_match = re.search(r'(\d+\.\d+\.\d+)', last_tag)
            if version_match:
                previous_version = version_match.group(1)
        
        # Use OpenAI to generate release notes
        try:
            generator = LLMReleaseNotesGenerator(api_key)
            release_notes = generator.generate_release_notes(commits, version, codename, previous_version)
            print(f"✅ Generated AI release notes using OpenAI")
            return release_notes
        except Exception as e:
            print(f"❌ OpenAI generation failed: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Failed to generate AI release notes: {e}")
        return None


if __name__ == "__main__":
    # Test the functionality
    import sys
    
    if len(sys.argv) > 1:
        test_version = sys.argv[1]
        test_codename = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"🧪 Testing release notes generation for version {test_version}")
        notes = generate_ai_release_notes(test_version, test_codename)
        
        if notes:
            print("\n" + "="*60)
            print("GENERATED RELEASE NOTES:")
            print("="*60)
            print(notes)
        else:
            print("❌ Failed to generate release notes")
    else:
        # Show recent commits for testing
        commits, last_tag = get_commits_for_release_notes()
        print(f"\n📋 Recent commits since {last_tag}:")
        for commit in commits[:10]:
            print(f"  {commit}")