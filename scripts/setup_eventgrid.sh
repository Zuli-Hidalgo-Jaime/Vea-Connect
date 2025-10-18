#!/bin/bash
# Event Grid Setup Script for WhatsApp ACS Advanced Messaging
# Usage: ./setup_eventgrid.sh SUB_ID RG ACS_NAME SUBS_NAME FUNCTION_URL FUNCTION_KEY

set -euo pipefail

# Check if all required parameters are provided
if [ $# -ne 6 ]; then
    echo "Usage: $0 SUB_ID RG ACS_NAME SUBS_NAME FUNCTION_URL FUNCTION_KEY"
    echo ""
    echo "Parameters:"
    echo "  SUB_ID       - Azure Subscription ID"
    echo "  RG           - Resource Group name"
    echo "  ACS_NAME     - Azure Communication Services name"
    echo "  SUBS_NAME    - Event Grid subscription name"
    echo "  FUNCTION_URL - Azure Function App URL"
    echo "  FUNCTION_KEY - Function key for authentication"
    echo ""
    echo "To get FUNCTION_KEY, run:"
    echo "  az functionapp function keys list --name <FUNCTION_APP_NAME> --resource-group <RG> --function-name whatsapp_event_grid_trigger --query 'default' -o tsv"
    exit 1
fi

# Parse parameters
SUB_ID="$1"
RG="$2"
ACS_NAME="$3"
SUBS_NAME="$4"
FUNCTION_URL="$5"
FUNCTION_KEY="$6"

# Construct ACS resource ID
ACS_ID="/subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.Communication/communicationServices/$ACS_NAME"

echo "Setting up Event Grid subscription for WhatsApp ACS Advanced Messaging"
echo "======================================================================"
echo "Subscription ID: $SUB_ID"
echo "Resource Group: $RG"
echo "ACS Name: $ACS_NAME"
echo "ACS Resource ID: $ACS_ID"
echo "Subscription Name: $SUBS_NAME"
echo "Function URL: $FUNCTION_URL"
echo ""

# Verify Azure CLI is available
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed or not in PATH"
    exit 1
fi

# Verify authentication
echo "Verifying Azure authentication..."
if ! az account show &> /dev/null; then
    echo "Error: Not authenticated with Azure. Run 'az login' first"
    exit 1
fi

# Check if ACS resource exists
echo "Verifying ACS resource exists..."
if ! az resource show --ids "$ACS_ID" &> /dev/null; then
    echo "Error: ACS resource not found: $ACS_ID"
    exit 1
fi

# Construct function endpoint URL
FUNCTION_ENDPOINT="$FUNCTION_URL/runtime/webhooks/eventgrid?functionName=whatsapp_event_grid_trigger&code=$FUNCTION_KEY"

echo "Function endpoint: $FUNCTION_ENDPOINT"
echo ""

# Create or update Event Grid subscription
echo "Creating/updating Event Grid subscription..."

# Check if subscription already exists
if az eventgrid event-subscription show --name "$SUBS_NAME" --source-resource-id "$ACS_ID" &> /dev/null; then
    echo "Subscription '$SUBS_NAME' already exists. Updating..."
    
    az eventgrid event-subscription update \
        --name "$SUBS_NAME" \
        --source-resource-id "$ACS_ID" \
        --endpoint-type webhook \
        --endpoint "$FUNCTION_ENDPOINT" \
        --included-event-types "Microsoft.Communication.AdvancedMessageReceived"
else
    echo "Creating new subscription '$SUBS_NAME'..."
    
    az eventgrid event-subscription create \
        --name "$SUBS_NAME" \
        --source-resource-id "$ACS_ID" \
        --endpoint-type webhook \
        --endpoint "$FUNCTION_ENDPOINT" \
        --included-event-types "Microsoft.Communication.AdvancedMessageReceived"
fi

# Verify subscription was created/updated
echo ""
echo "Verifying subscription configuration..."

SUBSCRIPTION_INFO=$(az eventgrid event-subscription show \
    --name "$SUBS_NAME" \
    --source-resource-id "$ACS_ID" \
    --output json)

# Extract and display event types
EVENT_TYPES=$(echo "$SUBSCRIPTION_INFO" | jq -r '.filter.includedEventTypes[]')
echo "Event Types:"
echo "$EVENT_TYPES" | while read -r event_type; do
    echo "  - $event_type"
done

# Extract and display endpoint URL
ENDPOINT_URL=$(echo "$SUBSCRIPTION_INFO" | jq -r '.destination.endpointUrl')
echo ""
echo "Endpoint URL:"
echo "  $ENDPOINT_URL"

echo ""
echo "Event Grid subscription setup completed successfully!"
echo ""
echo "To test the setup:"
echo "1. Send a WhatsApp message to your ACS number"
echo "2. Check Function App logs for incoming events"
echo "3. Verify the function processes the message correctly"
