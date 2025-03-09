#!/bin/bash
# Script to set up GitHub repository and push all branches

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}CR2 Project Creator GitHub Setup Script${NC}"
echo -e "${YELLOW}--------------------------------------${NC}"

# Use the correct repository name
REPO_NAME="CR2-Project-Creator"  # Updated to match the name user created
GITHUB_USERNAME="craigrusso"  

echo -e "${GREEN}Setting up GitHub repository: ${REPO_NAME}${NC}"

# Remove any existing origin
echo "Removing existing remote origin (if any)..."
git remote remove origin

# Add the remote using HTTPS (more reliable than SSH for most users)
echo "Adding remote origin with HTTPS..."
git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

# List branches
echo -e "${GREEN}Branches to push:${NC}"
git branch

# Push all branches
echo -e "${GREEN}Pushing all branches to GitHub...${NC}"
echo "Note: You may be prompted for your GitHub credentials."
echo "Use your GitHub username and Personal Access Token (not your password)."

# Push prod branch
echo "Pushing prod branch..."
git push -u origin prod

# Push dev branch
echo "Pushing dev branch..."
git push -u origin dev

# Push testing branch
echo "Pushing testing branch..."
git push -u origin testing

echo -e "${GREEN}Setup complete!${NC}"
echo -e "Repository URL: ${YELLOW}https://github.com/${GITHUB_USERNAME}/${REPO_NAME}${NC}"
echo -e "${YELLOW}Before running this script, make sure you have:${NC}"
echo "1. Created a repository named ${REPO_NAME} on GitHub"
echo "2. The repository should be empty (no README, .gitignore, etc.)"
echo "3. You have permission to push to this repository" 