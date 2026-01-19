#!/usr/bin/env python
"""
Quick Setup Script for DopeEvents Production Deployment
This script helps you set up Cloudinary and prepare for deployment
"""

import os
import sys

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print('='*60)

def print_step(step, title):
    """Print formatted step"""
    print(f"\n📋 Step {step}: {title}")
    print('-' * 40)

def check_cloudinary_setup():
    """Check if Cloudinary is properly configured"""
    print_step(1, "Cloudinary Setup Check")
    
    # Check if .env file exists
    env_file = '.env'
    if os.path.exists(env_file):
        print(f"✅ Found {env_file} file")
        
        # Read and check Cloudinary variables
        with open(env_file, 'r') as f:
            content = f.read()
            
        cloudinary_vars = [
            'CLOUDINARY_CLOUD_NAME',
            'CLOUDINARY_API_KEY', 
            'CLOUDINARY_API_SECRET'
        ]
        
        missing_vars = []
        for var in cloudinary_vars:
            if var not in content or f'{var}=' in content and content.split(f'{var}=')[1].strip() == '':
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing Cloudinary variables: {', '.join(missing_vars)}")
            print("💡 Get these from: https://cloudinary.com/console")
            return False
        else:
            print("✅ Cloudinary variables are configured")
            return True
    else:
        print(f"❌ {env_file} file not found")
        print("💡 Create .env file with Cloudinary credentials")
        return False

def check_supabase_setup():
    """Check if Supabase is properly configured"""
    print_step(2, "Supabase Database Setup Check")
    
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
            
        supabase_vars = [
            'SUPABASE_DB_NAME',
            'SUPABASE_DB_USER',
            'SUPABASE_DB_PASSWORD',
            'SUPabase_DB_HOST'
        ]
        
        missing_vars = []
        for var in supabase_vars:
            if var not in content or f'{var}=' in content and content.split(f'{var}=')[1].strip() == '':
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing Supabase variables: {', '.join(missing_vars)}")
            print("💡 Get these from: https://supabase.com/dashboard")
            return False
        else:
            print("✅ Supabase variables are configured")
            return True
    else:
        print(f"❌ {env_file} file not found")
        return False

def create_production_env():
    """Create production environment file"""
    print_step(3, "Create Production Environment")
    
    if not os.path.exists('.env.production'):
        print("✅ .env.production already exists")
        return True
    
    # Copy from template
    if os.path.exists('.env.production'):
        print("✅ Production environment file exists")
        return True
    else:
        print("❌ .env.production not found")
        print("💡 Use the .env.production template provided")
        return False

def run_tests():
    """Run Cloudinary tests"""
    print_step(4, "Run Cloudinary Tests")
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'test_cloudinary.py'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ Cloudinary tests passed")
            print(result.stdout)
            return True
        else:
            print("❌ Cloudinary tests failed")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def deployment_checklist():
    """Show deployment checklist"""
    print_step(5, "Deployment Checklist")
    
    checklist = [
        "☐ Create Cloudinary account and get credentials",
        "☐ Create Supabase project and get database credentials",
        "☐ Update .env.production with actual credentials",
        "☐ Push code to GitHub repository",
        "☐ Create Render account and connect repository",
        "☐ Configure environment variables in Render",
        "☐ Deploy to Render",
        "☐ Run migration script: python migrate_to_supabase.py",
        "☐ Test image uploads in production",
        "☐ Configure custom domain (optional)"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print(f"\n📚 Full guide: DEPLOYMENT.md")

def main():
    """Main setup function"""
    print_header("DopeEvents Production Setup Assistant")
    
    print("This script will help you prepare your DopeEvents application for production deployment.")
    print("It will check Cloudinary and Supabase configurations and run tests.")
    
    # Run checks
    cloudinary_ok = check_cloudinary_setup()
    supabase_ok = check_supabase_setup()
    env_ok = create_production_env()
    tests_ok = run_tests()
    
    # Show summary
    print_header("Setup Summary")
    
    print(f"Cloudinary Setup: {'✅ Ready' if cloudinary_ok else '⚠️  Needs Configuration'}")
    print(f"Supabase Setup: {'✅ Ready' if supabase_ok else '⚠️  Needs Configuration'}")
    print(f"Environment Files: {'✅ Ready' if env_ok else '⚠️  Needs Configuration'}")
    print(f"Tests: {'✅ Passed' if tests_ok else '⚠️  Failed'}")
    
    # Show next steps
    if all([cloudinary_ok, supabase_ok, env_ok, tests_ok]):
        print("\n🎉 You're ready for production deployment!")
        print("Follow the deployment checklist above.")
    else:
        print("\n⚠️  Some setup steps need to be completed.")
        print("Follow the deployment checklist above to finish setup.")
    
    deployment_checklist()

if __name__ == '__main__':
    main()
