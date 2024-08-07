#!/bin/bash

set -e

while getopts ":j:h" opt; do
  case ${opt} in
    j )
      JSON_FILE=$OPTARG
      ;;
    h )
      echo "Usage: $0 [-j <json_file>]"
      exit 0
      ;;
    \? )
      echo "Invalid option: $OPTARG" 1>&2
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument" 1>&2
      ;;
  esac
done
shift $((OPTIND -1))

if [[ -z "$JSON_FILE" ]]; then
  echo "JSON file path is required"
  exit 1
fi

# Get the directory containing the JSON file
JSON_DIR=$(dirname "$JSON_FILE")

# Create the directory if it doesn't exist
if [[ ! -d "$JSON_DIR" ]]; then
  mkdir -p "$JSON_DIR"
fi

# Change to the directory containing the JSON file
cd "$JSON_DIR" || { echo "Could not change directory to $JSON_DIR"; exit 1; }

# Check if the JSON file exists and is not empty
if [[ ! -s "$(basename "$JSON_FILE")" ]]; then
  echo "Creating new JSON file: $JSON_FILE"
  echo "[]" > "$(basename "$JSON_FILE")"
fi

# Read the existing JSON file
json_content=$(cat "$(basename "$JSON_FILE")")

# Get the root OU ID
ROOT_OU_ID=$(aws organizations list-roots --query 'Roots[0].Id' --output text)

# Get the IAM Identity Store ID and ARN
IDENTITY_STORE_ARN=$(aws sso-admin list-instances --query 'Instances[?InstanceArn!=`null`].InstanceArn' --output text)
IDENTITY_STORE_ID=$(aws sso-admin list-instances --query 'Instances[?IdentityStoreId!=`null`].IdentityStoreId' --output text)

# Add the new entries to the JSON array
json_content=$(jq --arg key "RootOUId" --arg value "$ROOT_OU_ID" '.+=[{"ParameterKey":$key,"ParameterValue":$value}]' <<< "$json_content")
json_content=$(jq --arg key "IdentityStoreId" --arg value "$IDENTITY_STORE_ID" '.+=[{"ParameterKey":$key,"ParameterValue":$value}]' <<< "$json_content")
json_content=$(jq --arg key "IdentityStoreArn" --arg value "$IDENTITY_STORE_ARN" '.+=[{"ParameterKey":$key,"ParameterValue":$value}]' <<< "$json_content")

# Write the updated JSON content back to the file
echo "$json_content" > "$(basename "$JSON_FILE")"

echo "JSON file updated successfully"
