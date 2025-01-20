import git
import random
from datetime import datetime, timedelta
from faker import Faker
import os
from collections import defaultdict

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

def rebase_repo(repo_url, output_dir, new_name, new_email):
    """Rebase repository with new author info and redistributed dates"""
    # Clone the repo
    print(f"Cloning {repo_url}...")
    repo = git.Repo.clone_from(repo_url, output_dir)
    
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
    
    # Create new commits with updated author info and dates
    print("Rebasing commits...")
    for i, commit in enumerate(commits):
        # Create new commit message
        message = commit.message
        
        # Create new commit with updated author info and date
        new_date = commit_dates[i]
        env = os.environ.copy()
        env['GIT_AUTHOR_DATE'] = new_date.isoformat()
        env['GIT_COMMITTER_DATE'] = new_date.isoformat()
        
        # Create new commit
        repo.git.commit(
            '--amend',
            '--no-edit',
            author=f"{new_name} <{new_email}>",
            env=env
        )
    
    print(f"Rebase complete! Repository saved to {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Rebase a GitHub repository with new author info and natural-looking commit dates")
    parser.add_argument('url', help='GitHub repository URL')
    parser.add_argument('output_dir', help='Output directory for cloned repository')
    parser.add_argument('--name', required=True, help='New author name')
    parser.add_argument('--email', required=True, help='New author email')
    
    args = parser.parse_args()
    
    rebase_repo(
        repo_url=args.url,
        output_dir=args.output_dir,
        new_name=args.name,
        new_email=args.email
    )
