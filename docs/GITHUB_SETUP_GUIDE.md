# GitHub Setup Guide

This guide will help you push your code to GitHub and set up proper branch structure.

## Step 1: Create a GitHub Repository

1. Go to https://github.com/new
2. Set the repository name to "CR2-Project-Creator"
3. Add a description (optional) 
4. Choose Public or Private visibility
5. DO NOT initialize with README, license, or .gitignore files
6. Click "Create repository"

## Step 2: Set Up Your Repository Locally

Run these commands in your terminal (one by one):

```bash
# Remove any existing remote
git remote remove origin

# Add GitHub as remote using HTTPS
git remote add origin https://github.com/craigrusso/CR2-Project-Creator.git

# Push the prod branch
git push -u origin prod

# Push the dev branch 
git push -u origin dev

# Push the testing branch
git push -u origin testing
```

When pushing, you'll be prompted for your GitHub username and password. 
For the password, you'll need to use a Personal Access Token (PAT).

## Step 3: Create a Personal Access Token (if needed)

If you don't have a Personal Access Token:

1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name like "CR2 Project Creator"
4. Set expiration as needed
5. Check the "repo" permission
6. Click "Generate token"
7. COPY THE TOKEN IMMEDIATELY (you won't see it again)
8. Use this token as your password when pushing

## Step 4: Verify Branches on GitHub

1. Go to your repository on GitHub (https://github.com/craigrusso/CR2-Project-Creator)
2. Click on the "branches" link to see all branches 
3. Confirm that prod, dev, and testing branches are present

## Step 5: Set Default Branch (Optional)

1. Go to your repository settings
2. Click on "Branches" in the left sidebar
3. Under "Default branch", change from "prod" to whichever branch you prefer
4. Click "Update"

## Branch Strategy

- **prod**: Production-ready code, stable releases
- **dev**: Development branch, features ready for integration
- **testing**: For testing features before merging to dev

## Workflow Example

```bash
# Start a new feature from dev branch
git checkout dev
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push feature branch to GitHub
git push -u origin feature/new-feature

# After code review, merge to testing (for integration testing)
git checkout testing
git merge feature/new-feature
git push

# After testing, merge to dev
git checkout dev
git merge feature/new-feature
git push

# For a release, merge dev to prod
git checkout prod
git merge dev
git push
``` 