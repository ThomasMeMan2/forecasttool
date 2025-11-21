"""
Code Analysis Script
Checks for potential issues without running the server
"""
import ast
import sys
from pathlib import Path

issues = []
warnings = []


def analyze_file(filepath):
    """Analyze a Python file for issues"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Check if file can be parsed
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"SYNTAX ERROR in {filepath}: {e}")
            return

        # Check for common issues
        if 'from jose import' in content and 'python-jose' not in str(filepath):
            warnings.append(f"{filepath}: Uses 'jose' - ensure python-jose[cryptography] is installed")

        if 'from passlib import' in content:
            warnings.append(f"{filepath}: Uses 'passlib' - ensure passlib[bcrypt] is installed")

        if 'Depends(get_current_user)' in content and 'optional' not in content.lower():
            warnings.append(f"{filepath}: Has protected endpoints requiring authentication")

        # Check for potential issues in auth.py
        if 'auth.py' in str(filepath):
            if 'SECRET_KEY' in content and 'your-secret-key' in content:
                issues.append(f"{filepath}: Uses default SECRET_KEY - security risk!")

            if 'get_current_user' in content and 'async def' in content:
                print(f"✓ {filepath}: Authentication dependency defined")

        # Check for Phase 4 models
        if 'models.py' in str(filepath):
            if 'ProjectShare' in content:
                print(f"✓ {filepath}: Phase 4 models defined")
            if 'class User' in content and 'hashed_password' in content:
                print(f"✓ {filepath}: User model has password field")

    except Exception as e:
        issues.append(f"ERROR analyzing {filepath}: {e}")


def check_requirements():
    """Check requirements.txt"""
    req_file = Path("backend/requirements.txt")
    if req_file.exists():
        with open(req_file) as f:
            requirements = f.read()

        required_packages = [
            ('python-jose', 'JWT authentication'),
            ('passlib', 'Password hashing'),
            ('statsforecast', 'Forecasting'),
            ('prophet', 'Prophet model'),
            ('fastapi', 'API framework')
        ]

        print("\n📦 Checking Requirements:")
        for package, purpose in required_packages:
            if package in requirements:
                print(f"  ✓ {package} - {purpose}")
            else:
                issues.append(f"Missing {package} in requirements.txt - needed for {purpose}")
    else:
        issues.append("requirements.txt not found!")


def check_env_example():
    """Check if .env.example exists"""
    env_file = Path("backend/.env.example")
    if env_file.exists():
        with open(env_file) as f:
            env_content = f.read()

        print("\n🔐 Checking Environment Configuration:")
        required_vars = ['DATABASE_URL', 'SECRET_KEY']
        for var in required_vars:
            if var in env_content:
                print(f"  ✓ {var} defined")
            else:
                warnings.append(f".env.example missing {var}")
    else:
        warnings.append(".env.example not found - users won't know what to configure")


def check_config():
    """Check config.py"""
    config_file = Path("backend/app/config.py")
    if config_file.exists():
        with open(config_file) as f:
            content = f.read()

        print("\n⚙️  Checking Configuration:")
        if 'secret_key' in content:
            print("  ✓ secret_key configuration exists")
        if 'database_url' in content:
            print("  ✓ database_url configuration exists")
    else:
        issues.append("config.py not found!")


def main():
    print("="*60)
    print("FORECAST STUDIO - CODE ANALYSIS")
    print("="*60)

    # Check requirements
    check_requirements()

    # Check configuration
    check_env_example()
    check_config()

    # Analyze Python files
    print("\n📝 Analyzing Python Files:")
    backend_path = Path("backend/app")
    if backend_path.exists():
        python_files = list(backend_path.rglob("*.py"))
        print(f"  Found {len(python_files)} Python files")

        for filepath in python_files:
            if '__pycache__' not in str(filepath):
                analyze_file(filepath)
    else:
        issues.append("backend/app directory not found!")

    # Print results
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)

    if issues:
        print(f"\n❌ CRITICAL ISSUES ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✅ No critical issues found!")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    if not issues and not warnings:
        print("\n🎉 Code analysis complete - everything looks good!")

    return len(issues)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
