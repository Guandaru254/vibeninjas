#!/usr/bin/env python
"""
Security Check Script for DopeEvents
Checks for exposed secrets and sensitive data before committing
"""

import os
import re
import sys
from pathlib import Path

def check_for_secrets():
    """Check for exposed secrets in the codebase"""
    
    print("🔒 Security Check - Looking for Exposed Secrets")
    print("=" * 60)
    
    # Patterns that should not be in code
    secret_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'Password assignment'),
        (r'secret[_]?key\s*=\s*["\'][^"\']+["\']', 'Secret key assignment'),
        (r'api[_]?key\s*=\s*["\'][^"\']+["\']', 'API key assignment'),
        (r'token\s*=\s*["\'][^"\']+["\']', 'Token assignment'),
        (r'cloudinary[_]?secret\s*=\s*["\'][^"\']+["\']', 'Cloudinary secret'),
        (r'supabase[_]?password\s*=\s*["\'][^"\']+["\']', 'Supabase password'),
        (r'stripe[_]?secret\s*=\s*["\'][^"\']+["\']', 'Stripe secret'),
        (r'twilio[_]?token\s*=\s*["\'][^"\']+["\']', 'Twilio token'),
        (r'mpesa[_]?secret\s*=\s*["\'][^"\']+["\']', 'M-Pesa secret'),
        (r'@@@Manuu@254#', 'Specific password found'),
        (r'499634162687969', 'Cloudinary API key'),
        (r'qREMsnfm9iKvonj75pbUUMtUIFU', 'Cloudinary secret'),
        (r'dvjvwfhtp', 'Cloudinary cloud name'),
        (r'db\.ftlxxxtbalmdtheqzzlm\.supabase\.co', 'Supabase host'),
    ]
    
    # Files to check
    file_extensions = ['.py', '.js', '.html', '.css', '.json', '.yaml', '.yml', '.md', '.txt']
    files_to_check = []
    
    # Files that should be ignored (contain secrets intentionally)
    ignored_files = {
        'CREDENTIALS_REFERENCE.md',
        'SECURITY_NOTES.md',
        'security_check.py'  # This file contains the patterns for checking
    }
    
    # Get all files to check
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['env', 'venv', '__pycache__', 'node_modules']]
        
        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                if not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    # Skip ignored files
                    if file not in ignored_files and 'security_check.py' not in file_path:
                        files_to_check.append(file_path)
    
    issues_found = []
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                line_number = 0
                
                for line in content.split('\n'):
                    line_number += 1
                    
                    for pattern, description in secret_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            issues_found.append({
                                'file': file_path,
                                'line': line_number,
                                'content': line.strip(),
                                'pattern': description
                            })
        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
    
    # Report findings
    if issues_found:
        print(f"❌ Found {len(issues_found)} potential security issues:")
        print()
        
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. 🚨 {issue['pattern']}")
            print(f"   📁 File: {issue['file']}")
            print(f"   📍 Line: {issue['line']}")
            print(f"   🔍 Content: {issue['content']}")
            print()
        
        print("⚠️  Please fix these issues before committing!")
        return False
    else:
        print("✅ No exposed secrets found in code!")
        return True

def check_gitignore():
    """Check if .gitignore exists and covers important files"""
    
    print("\n📋 Checking .gitignore coverage")
    print("=" * 40)
    
    gitignore_path = '.gitignore'
    
    if not os.path.exists(gitignore_path):
        print("❌ .gitignore file not found!")
        return False
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    required_patterns = [
        '.env',
        '*.log',
        '__pycache__/',
        'db.sqlite3',
        'media/',
        'staticfiles/',
        '*.pyc',
        '.DS_Store',
        'env/',
        'venv/',
    ]
    
    missing_patterns = []
    
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"⚠️  Missing patterns in .gitignore:")
        for pattern in missing_patterns:
            print(f"   - {pattern}")
        return False
    else:
        print("✅ .gitignore covers all important patterns!")
        return True

def check_sensitive_files():
    """Check for sensitive files that should not be committed"""
    
    print("\n🔍 Checking for sensitive files")
    print("=" * 40)
    
    # Read .gitignore to see what's being ignored
    gitignore_path = '.gitignore'
    ignored_patterns = set()
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignored_patterns.add(line)
    
    sensitive_files = [
        '.env',
        '.env.production',
        '.env.development',
        'local_settings.py',
        'settings_local.py',
        'credentials.json',
        'secrets.json',
        'config.json',
        'id_rsa',
        'id_rsa.pub',
        '*.pem',
        '*.key',
    ]
    
    found_unignored = []
    found_ignored = []
    
    for pattern in sensitive_files:
        if '*' in pattern:
            import glob
            matches = glob.glob(pattern)
            for match in matches:
                if any(match.startswith(p.strip('/')) or match.endswith(p.strip('/')) or p.strip('/') in match for p in ignored_patterns):
                    found_ignored.append(match)
                else:
                    found_unignored.append(match)
        elif os.path.exists(pattern):
            if any(pattern == p.strip('/') or pattern.endswith(p.strip('/')) for p in ignored_patterns):
                found_ignored.append(pattern)
            else:
                found_unignored.append(pattern)
    
    if found_unignored:
        print(f"❌ Found sensitive files that are NOT ignored:")
        for file_path in found_unignored:
            print(f"   - {file_path}")
        print("\n⚠️  Add these to your .gitignore immediately!")
        return False
    elif found_ignored:
        print(f"✅ Found {len(found_ignored)} sensitive files (properly ignored):")
        for file_path in found_ignored:
            print(f"   - {file_path}")
        print("\n✅ All sensitive files are protected by .gitignore!")
        return True
    else:
        print("✅ No sensitive files found!")
        return True

def main():
    """Main security check function"""
    
    print("🚀 DopeEvents Security Check")
    print("=" * 60)
    print("This script checks for exposed secrets and security issues")
    print("before you commit your code to Git.\n")
    
    # Run all checks
    secrets_ok = check_for_secrets()
    gitignore_ok = check_gitignore()
    files_ok = check_sensitive_files()
    
    # Summary
    print("\n📊 Security Check Summary")
    print("=" * 30)
    print(f"Secrets Check: {'✅ Pass' if secrets_ok else '❌ Fail'}")
    print(f".gitignore Check: {'✅ Pass' if gitignore_ok else '❌ Fail'}")
    print(f"Sensitive Files: {'✅ Pass' if files_ok else '❌ Fail'}")
    
    if all([secrets_ok, gitignore_ok, files_ok]):
        print("\n🎉 All security checks passed! Safe to commit.")
        return 0
    else:
        print("\n⚠️  Please fix the security issues above before committing.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
