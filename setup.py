#!/usr/bin/env python3
"""
Setup script for LM Studio Context Size Benchmark
Helps users get started with the benchmark tool
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        print(f"   Error output: {e.stderr}")
        return False

def check_book_file():
    """Check if a book file exists"""
    books_dir = Path("books")
    
    # Look for any book files
    book_extensions = ['.pdf', '.txt', '.epub', '.docx', '.doc']
    book_files = []
    
    for ext in book_extensions:
        book_files.extend(books_dir.glob(f"*{ext}"))
    
    if book_files:
        print(f"\n📚 Found book files:")
        for book in book_files:
            print(f"   - {book}")
        
        # Check config
        try:
            from config_loader import load_config
            config = load_config()
            config_book = Path(config.book_path)
            
            if config_book.exists():
                print(f"✅ Configuration points to existing book: {config_book}")
            else:
                print(f"⚠️  Configuration points to missing book: {config_book}")
                print(f"   Update config.yaml to point to one of your book files")
        except Exception as e:
            print(f"⚠️  Could not check configuration: {e}")
        
        return True
    else:
        print(f"\n📚 No book files found in books/ directory")
        print(f"   Add a PDF, TXT, or other book file to books/")
        print(f"   See books/README.md for detailed instructions")
        return False

def check_lm_studio():
    """Check if LM Studio API is accessible"""
    print(f"\n🌐 Checking LM Studio API...")
    try:
        import requests
        response = requests.get("http://localhost:5002/v1/models", timeout=5)
        
        if response.status_code == 200:
            models = response.json()
            model_count = len(models.get('data', []))
            print(f"✅ LM Studio API accessible with {model_count} models")
            
            # Show available models
            if model_count > 0:
                print(f"   Available models:")
                for model in models['data'][:5]:  # Show first 5
                    print(f"     - {model['id']}")
                if model_count > 5:
                    print(f"     ... and {model_count - 5} more")
            
            return True
        else:
            print(f"⚠️  LM Studio API responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to LM Studio API at http://localhost:5002")
        print(f"   Make sure LM Studio is running with API enabled")
        return False
    except ImportError:
        print(f"⚠️  Cannot check LM Studio (requests not installed yet)")
        return False
    except Exception as e:
        print(f"❌ Error checking LM Studio: {e}")
        return False

def validate_configuration():
    """Validate the configuration file"""
    print(f"\n⚙️  Validating configuration...")
    try:
        from config_loader import load_config, validate_config
        config = load_config()
        issues = validate_config(config)
        
        if not issues:
            print(f"✅ Configuration is valid")
            print(f"   Models to test: {len(config.models)}")
            print(f"   Context sizes: {len(config.context_sizes)}")
            return True
        else:
            print(f"❌ Configuration issues:")
            for issue in issues:
                print(f"   - {issue}")
            return False
            
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False

def show_next_steps(all_checks_passed):
    """Show what to do next"""
    print(f"\n" + "="*60)
    print(f"SETUP SUMMARY")
    print(f"="*60)
    
    if all_checks_passed:
        print(f"🎉 Setup completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Run a quick test:")
        print(f"   python config_loader.py")
        print(f"\n2. Start benchmarking:")
        print(f"   python multi_model_benchmark.py")
        print(f"\n3. View results:")
        print(f"   python list_results.py")
        print(f"\n4. Generate charts:")
        print(f"   python create_final_charts.py")
    else:
        print(f"⚠️  Setup needs attention")
        print(f"\nPlease fix the issues above, then:")
        print(f"1. Run setup again: python setup.py")
        print(f"2. Or proceed manually if you understand the issues")

def main():
    """Main setup function"""
    print("🔥 LM Studio Context Size Benchmark - Setup")
    print("="*60)
    
    checks = []
    
    # Run all checks
    checks.append(("Python Version", check_python_version()))
    checks.append(("Install Requirements", install_requirements()))
    checks.append(("Book File", check_book_file()))
    checks.append(("LM Studio API", check_lm_studio()))
    checks.append(("Configuration", validate_configuration()))
    
    # Summary
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    all_passed = passed == total
    
    print(f"\n📋 Setup Results: {passed}/{total} checks passed")
    for name, result in checks:
        status = "✅" if result else "❌"
        print(f"   {status} {name}")
    
    show_next_steps(all_passed)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
