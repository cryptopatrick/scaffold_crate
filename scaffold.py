#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path


def get_user_input():
    """Prompt user for crate details."""
    print("Rust Crate Scaffolding Tool")
    print("=" * 30)

    crate_name = input("Enter crate name: ").strip()
    if not crate_name:
        print("Error: Crate name cannot be empty")
        sys.exit(1)

    description = input("Enter description: ").strip()
    if not description:
        print("Error: Description cannot be empty")
        sys.exit(1)

    keywords = input("Enter keywords (comma-separated): ").strip()
    if not keywords:
        print("Error: Keywords cannot be empty")
        sys.exit(1)

    return crate_name, description, keywords


def copy_payload_folder(crate_name):
    """Copy the payload folder and rename it to crate_name."""
    script_dir = Path(__file__).parent
    payload_dir = script_dir / "payload"
    target_dir = script_dir / crate_name

    if not payload_dir.exists():
        print(f"Error: payload folder not found at {payload_dir}")
        sys.exit(1)

    if target_dir.exists():
        print(f"Error: Directory {crate_name} already exists")
        sys.exit(1)

    print(f"Copying payload folder to {crate_name}...")
    shutil.copytree(payload_dir, target_dir)
    return target_dir


def replace_placeholders(target_dir, crate_name, description, keywords):
    """Replace placeholders in all files within the target directory."""
    print("Replacing placeholders in files...")

    replacements = {
        "<CRATE_NAME>": crate_name,
        "<DESCRIPTION>": description,
        "<KEYWORDS>": keywords
    }

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            file_path = Path(root) / file

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                for placeholder, replacement in replacements.items():
                    content = content.replace(placeholder, replacement)

                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated: {file_path}")

            except (UnicodeDecodeError, PermissionError):
                print(f"Skipping binary or protected file: {file_path}")


def setup_github_repo(crate_name):
    """Create GitHub repository and set up the project."""
    print(f"Setting up GitHub repository for {crate_name}...")

    crt_dir = Path.home() / "wer" / "crt"

    if not crt_dir.exists():
        print(f"Error: Directory {crt_dir} does not exist")
        sys.exit(1)

    try:
        os.chdir(crt_dir)

        subprocess.run(["gh", "repo", "create", crate_name, "--public"], check=True)

        subprocess.run(["git", "clone", f"https://github.com/{get_github_username()}/{crate_name}.git"], check=True)

        crate_dir = crt_dir / crate_name
        source_dir = crt_dir / "scaffold_crate" / crate_name

        os.chdir(crate_dir)

        for item in source_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, crate_dir)
            elif item.is_dir():
                shutil.copytree(item, crate_dir / item.name)

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit."], check=True)

        # Get the current branch name
        result = subprocess.run(["git", "branch", "--show-current"],
                              capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()

        subprocess.run(["git", "push", "origin", current_branch], check=True)

        print(f"Successfully created and set up repository: {crate_name}")
        print(f"Repository URL: https://github.com/{get_github_username()}/{crate_name}")

    except subprocess.CalledProcessError as e:
        print(f"Error during GitHub setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def get_github_username():
    """Get the current GitHub username."""
    try:
        result = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Error: Could not get GitHub username. Make sure you're logged in with 'gh auth login'")
        sys.exit(1)


def main():
    """Main function to orchestrate the scaffolding process."""
    try:
        crate_name, description, keywords = get_user_input()

        target_dir = copy_payload_folder(crate_name)

        replace_placeholders(target_dir, crate_name, description, keywords)

        setup_github_repo(crate_name)

        # Clean up: remove the local copy of the crate folder
        print(f"Cleaning up local copy...")
        shutil.rmtree(target_dir)

        print(f"\n✅ Successfully scaffolded Rust crate: {crate_name}")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
