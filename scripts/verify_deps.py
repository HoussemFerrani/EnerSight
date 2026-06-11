"""Verify new dependencies are installed"""

packages_to_check = [
    "asyncpg",
    "aiosqlite", 
    "pytest_cov",
    "pytest_mock",
    "mypy",
    "isort",
]

print("Checking installed packages...\n")

all_installed = True
for package in packages_to_check:
    try:
        __import__(package)
        print(f"✅ {package:15} - Installed")
    except ImportError:
        print(f"❌ {package:15} - NOT FOUND")
        all_installed = False

print("\n" + "="*40)
if all_installed:
    print("✅ ALL DEPENDENCIES INSTALLED SUCCESSFULLY!")
else:
    print("❌ Some packages are missing. Run:")
    print("   py -3.11 -m pip install asyncpg aiosqlite pytest-cov pytest-mock mypy isort")
