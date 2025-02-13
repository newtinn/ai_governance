import os
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Authenticate using Azure CLI credentials
credential = AzureCliCredential()

# Retrieve your Azure subscription ID from environment variables
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

# Initialize the Resource Management client
resource_client = ResourceManagementClient(credential, subscription_id)

# Define the resource group name and location
rg_name = "PythonAzureExample-rg"
location = "uksouth"

# Create or update the resource group
rg_result = resource_client.resource_groups.create_or_update(
    rg_name, {"location": location}
)

print(f"Provisioned resource group {rg_result.name} in the {rg_result.location} region")
