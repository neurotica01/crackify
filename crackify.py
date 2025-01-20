import git
import random
from datetime import datetime, timedelta
from faker import Faker
import os
import subprocess
from collections import defaultdict
import requests

def get_weighted_date():
    """Generate a random date in the past year with weekend/evening bias"""
    fake = Faker()
    # Base date range - past year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Get a random date
    date = fake.date_time_between(start_date=start_date, end_date=end_date)
    
    # Weight adjustments
    if date.weekday() >= 5:  # Weekend
        date += timedelta(hours=random.randint(12, 23))  # Evening bias
    else:
        # Weekdays - 60% chance of evening (6pm-11pm)
        if random.random() < 0.6:
            date = date.replace(hour=random.randint(18, 23))
    
    return date

def get_git_config(key):
    """Get a git config value"""
    try:
        return subprocess.check_output(['git', 'config', '--global', key]).decode().strip()
    except subprocess.CalledProcessError:
        return None

def create_github_repo(repo_name, token):
    """Create a new repository on GitHub"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "private": False,
        "auto_init": False
    }
    response = requests.post("https://api.github.com/user/repos", json=data, headers=headers)
    if response.status_code != 201:
        raise Exception(f"Failed to create repository: {response.json().get('message', 'Unknown error')}")
    return response.json()['ssh_url']

def rebase_repo(repo_url, output_dir, new_name=None, new_email=None, push_url=None):
    """Rebase repository with new author info and redistributed dates"""
    # Clone the repo
    print(f"Cloning {repo_url}...")
    repo = git.Repo.clone_from(repo_url, output_dir)
    
    # Remove old origin if we're pushing to a new URL
    if push_url:
        repo.delete_remote('origin')
    
    # Try common branch names
    branch_names = ['main', 'master', 'stable']
    commits = []
    
    for branch in branch_names:
        try:
            commits = list(repo.iter_commits(branch))
            print(f"Using branch: {branch}")
            break
        except git.exc.GitCommandError:
            continue
            
    if not commits:
        raise Exception("Could not find any of the standard branches (main, master, stable)")
    
    # Generate new dates for all commits
    commit_dates = sorted([get_weighted_date() for _ in commits])
    
    # Create new branch for rebased commits
    repo.git.checkout('--orphan', 'rebased')
    
    # Create new commits with updated author info and dates
    print("Creating new commits...")
    for i, commit in enumerate(commits):
        # Create new commit message
        message = commit.message
        
        # Create new commit with updated author info and date
        new_date = commit_dates[i]
        env = os.environ.copy()
        env['GIT_AUTHOR_DATE'] = new_date.isoformat()
        env['GIT_COMMITTER_DATE'] = new_date.isoformat()
        
        # Reset to the original commit state
        repo.git.read_tree(commit.hexsha)
        repo.git.checkout_index('-a', '-f')
        
        # Create new commit
        repo.git.commit(
            '-m', message,
            author=f"{new_name} <{new_email}>",
            env=env
        )
    
    # Move rebased branch to main
    repo.git.branch('-M', 'rebased', 'main')
    
    print(f"Rebase complete! Repository saved to {output_dir}")
    
    # Push to new remote if requested
    if push_url:
        # Extract repo name from push URL
        repo_name = push_url.split('/')[-1].replace('.git', '')
        
        # Get GitHub token
        token = get_git_config('github.token')
        if not token:
            raise Exception("GitHub token not found. Please set with: git config --global github.token YOUR_TOKEN")
            
        # Create the repository on GitHub
        print(f"Creating new repository {repo_name} on GitHub...")
        actual_push_url = create_github_repo(repo_name, token)
        
        # Push to the new remote
        print(f"Pushing to new remote: {actual_push_url}")
        repo.create_remote('origin', actual_push_url)
        repo.git.push('origin', '--force', '--all')
        repo.git.push('origin', '--force', '--tags')
        print("Push complete! All branches and tags pushed to new remote.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Rebase a GitHub repository with new author info and natural-looking commit dates")
    parser.add_argument('url', help='GitHub repository URL')
    parser.add_argument('output_dir', help='Output directory for cloned repository')
    parser.add_argument('--name', help='New author name (default: git config user.name)')
    parser.add_argument('--email', help='New author email (default: git config user.email)')
    parser.add_argument('--push-url', help='URL to push the rebased repository to')
    
    args = parser.parse_args()
    
    # Get default values from git config
    if not args.name:
        args.name = get_git_config('user.name')
        if not args.name:
            raise Exception("No --name provided and git config user.name not set")
            
    if not args.email:
        args.email = get_git_config('user.email')
        if not args.email:
            raise Exception("No --email provided and git config user.email not set")
            
    # Prepare push URL if not provided
    if not args.push_url:
        username = get_git_config('github.user') or get_git_config('user.name')
        if not username:
            raise Exception("Could not determine GitHub username")
            
        # Extract repo name from URL
        repo_name = args.url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
            
        # Get GitHub token
        token = get_git_config('github.token')
        if not token:
            raise Exception("GitHub token not found. Please set with: git config --global github.token YOUR_TOKEN")
            
        # Generate the push URL but don't create the repo yet
        args.push_url = f"git@github.com:{username}/{repo_name}.git"

    rebase_repo(
        repo_url=args.url,
        output_dir=args.output_dir,
        new_name=args.name,
        new_email=args.email,
        push_url=args.push_url
    )
