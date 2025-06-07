#!/usr/bin/env bash

# Script to check and update .env file with missing variables

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

ENV_FILE=".env"
SAMPLE_FILE=".env.sample"

echo -e "${YELLOW}Checking .env file for missing variables...${NC}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: .env file not found.${NC}"
    echo -e "${YELLOW}Creating .env file from sample...${NC}"
    cp "$SAMPLE_FILE" "$ENV_FILE"
    echo -e "${GREEN}.env file created from sample. Please update the values.${NC}"
    exit 0
fi

if [ ! -f "$SAMPLE_FILE" ]; then
    echo -e "${RED}Error: .env.sample file not found.${NC}"
    exit 1
fi

# Read sample keys
SAMPLE_KEYS=$(grep -v '^#' "$SAMPLE_FILE" | cut -d '=' -f 1)
UPDATED=0

for key in $SAMPLE_KEYS; do
    if ! grep -q "^${key}=" "$ENV_FILE"; then
        # Get the value from sample
        value=$(grep "^${key}=" "$SAMPLE_FILE" | cut -d '=' -f 2-)
        echo -e "${YELLOW}Adding missing variable to .env: ${key}=${value}${NC}"
        echo "${key}=${value}" >> "$ENV_FILE"
        UPDATED=1
    fi
done

if [ $UPDATED -eq 1 ]; then
    echo -e "${GREEN}Updated .env file with missing variables.${NC}"
    echo -e "${YELLOW}Please review the values in your .env file.${NC}"
else
    echo -e "${GREEN}All sample variables are present in .env file.${NC}"
fi

# Reminders for important settings
echo
echo -e "${YELLOW}Important settings for patient invite system:${NC}"
echo -e "1. ${YELLOW}FRONTEND_URL${NC} - Make sure this is set to the correct URL (default: http://localhost:4321)"
echo -e "2. ${YELLOW}EMAIL_ENABLED${NC} - Set to 'true' to enable email notifications"
echo -e "3. ${YELLOW}SMTP_SERVER${NC}, ${YELLOW}SMTP_USERNAME${NC}, ${YELLOW}SMTP_PASSWORD${NC} - Required for email sending"

exit 0
