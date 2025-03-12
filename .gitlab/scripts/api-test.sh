#!/bin/bash
set -e

API_URL=$1
DATA_FILE=$2

if [ -z "$API_URL" ] || [ -z "$DATA_FILE" ]; then
  echo "Usage: $0 <api_url> <data_file>"
  echo "Example: $0 http://api.example.com data/addresses/namo.json"
  exit 1
fi

echo "Testing API at $API_URL using data from $DATA_FILE"

# Create an address entry
echo "Creating address entry..."
RESPONSE=$(curl -s -i -X POST "$API_URL/addresses" -H "Content-Type: application/json" -d "@$DATA_FILE")
echo "$RESPONSE"

# Extract the location header to get the ID
LOCATION=$(echo "$RESPONSE" | grep -i Location)
ADDRESS_ID=$(echo "$LOCATION" | cut -d'/' -f3)

if [ -z "$ADDRESS_ID" ]; then
  echo "Failed to get address ID from response"
  exit 1
fi

echo "Created address with ID: $ADDRESS_ID"

# Get the created address to verify it exists
echo -e "\nFetching created address..."
GET_RESPONSE=$(curl -s -X GET "$API_URL/addresses/$ADDRESS_ID")
echo "$GET_RESPONSE"

# Verify the address can be retrieved
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/addresses/$ADDRESS_ID")
if [ "$HTTP_STATUS" -eq 200 ]; then
  echo -e "\nAPI test succeeded: Address retrieved successfully with status $HTTP_STATUS"
else
  echo -e "\nAPI test failed: Could not retrieve address (Status: $HTTP_STATUS)"
  exit 1
fi

# Delete the address entry
echo -e "\nDeleting address entry..."
DELETE_RESPONSE=$(curl -s -i -X DELETE "$API_URL/addresses/$ADDRESS_ID")
DELETE_STATUS=$(echo "$DELETE_RESPONSE" | grep -i "HTTP" | awk '{print $2}')
echo "$DELETE_RESPONSE"

# Verify the address was deleted by attempting to fetch it again
echo -e "\nVerifying address was deleted..."
HTTP_STATUS_AFTER_DELETE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/addresses/$ADDRESS_ID")

if [ "$HTTP_STATUS_AFTER_DELETE" -eq 404 ]; then
  echo -e "\nAPI delete test succeeded: Address no longer exists (Status: $HTTP_STATUS_AFTER_DELETE)"
  
  # Also check if the address list is empty or doesn't contain our deleted ID
  ADDRESSES_LIST=$(curl -s -X GET "$API_URL/addresses")
  if [[ "$ADDRESSES_LIST" == "{}" || ! "$ADDRESSES_LIST" == *"$ADDRESS_ID"* ]]; then
    echo "Address list verification successful: Deleted address is not in the list"
    exit 0
  else
    echo "API test failed: Address still appears in address list after deletion"
    echo "Addresses list: $ADDRESSES_LIST"
    exit 1
  fi
else
  echo -e "\nAPI delete test failed: Address still exists after deletion attempt (Status: $HTTP_STATUS_AFTER_DELETE)"
  exit 1
fi
