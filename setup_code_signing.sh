#!/bin/bash
# Script to help set up code signing for Echelon

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}    Setting up code signing for Echelon - CR2 Creative${NC}"
echo -e "${BLUE}=======================================================${NC}"

# Check if we have existing certificates
echo -e "\n${YELLOW}Checking for existing code signing identities...${NC}"
security find-identity -v -p codesigning

# Create self-signed certificate files
echo -e "\n${YELLOW}Creating new self-signed certificate for code signing...${NC}"
openssl genrsa -out cr2_private.key 2048
openssl req -new -key cr2_private.key -out cr2_cert.csr -subj "/CN=CR2 Code Signing/O=CR2 Creative/C=US"
openssl x509 -req -in cr2_cert.csr -signkey cr2_private.key -out cr2_cert.crt -days 365

# Create P12 file
echo -e "\n${YELLOW}Creating PKCS#12 file (will be password protected)...${NC}"
echo -e "${GREEN}Enter a password to protect your code signing certificate:${NC}"
read -s PASSWORD
openssl pkcs12 -export -out cr2_code_signing.p12 -inkey cr2_private.key -in cr2_cert.crt -name "CR2 Code Signing" -passout pass:"$PASSWORD"

echo -e "\n${GREEN}Certificate files created:${NC}"
echo "  - cr2_private.key (private key - keep secure)"
echo "  - cr2_cert.crt (certificate)"
echo "  - cr2_code_signing.p12 (combined certificate and key for import)"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Open Keychain Access (search for it in Spotlight)"
echo "2. In Keychain Access, select File > Import Items..."
echo "3. Select the cr2_code_signing.p12 file"
echo "4. Enter the password you created"
echo "5. The certificate will be imported into your keychain"

echo -e "\n${YELLOW}After importing, check that the certificate appears:${NC}"
echo "security find-identity -v -p codesigning"

echo -e "\n${BLUE}=======================================================${NC}"
echo -e "${GREEN}To sign the Echelon app, run:${NC}"
echo "codesign --force --deep --sign \"CR2 Code Signing\" dist/Echelon.app"
echo -e "${BLUE}=======================================================${NC}" 