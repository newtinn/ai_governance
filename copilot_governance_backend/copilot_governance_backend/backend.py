from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.consumption.models import Budget, BudgetTimePeriod, Notification
from azure.mgmt.storage import StorageManagementClient
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Workspace
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import Account, Sku, Deployment, DeploymentModel, DeploymentProperties
from azure.storage.blob import BlobServiceClient
from azure.core.polling import LROPoller
from azure.core.exceptions import HttpResponseError
from openai import AzureOpenAI

from azure.core.exceptions import ResourceExistsError
from datetime import datetime, timezone
import os

from models import Agent, Base
from database import engine, get_db
from sqlalchemy.orm import Session

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

credentials = AzureCliCredential()
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

resource_client = ResourceManagementClient(credentials, subscription_id)
consumption_client = ConsumptionManagementClient(credentials, subscription_id)
storage_client = StorageManagementClient(credentials, subscription_id)
cognitive_client = CognitiveServicesManagementClient(credentials, subscription_id)

class ResourceGroup(BaseModel):
    name: str
    display_name: str
    description: str
    owner: str
    owner_email: str
    model_base: str
    location: str
    active: bool
    status: str
    budget: float

def get_openai_api_key(subscription_id, resource_group_name, resource_name):
    # Initialize the Cognitive Services Management Client
    cognitive_client = CognitiveServicesManagementClient(credentials, subscription_id)

    # Retrieve the API keys for the specified Cognitive Services resource
    keys = cognitive_client.accounts.list_keys(resource_group_name, resource_name)

    # Return the primary API key
    return keys.key1

def deploy_openai_model(cognitive_client, resource_group_name, openai_resource_name, deployment_name, model_name):
    try:
        # Define the deployment model
        deployment_model = DeploymentModel(
            name=model_name,       # Use the correct model name (e.g., 'gpt-4', 'gpt-35-turbo')
            format='OpenAI',       # The format of the model
            version='0613',        # Use the correct version (if required)
            publisher='OpenAI'     # The publisher of the model
        )

        # Define the deployment properties
        deployment_properties = DeploymentProperties(
            model=deployment_model
        )

        # Define the SKU for the deployment
        deployment_sku = Sku(
            name='Standard',  # Use the correct SKU name (e.g., 'Standard', 'Premium')
            capacity=1        # Adjust capacity as needed
        )

        # Define the deployment
        deployment = Deployment(
            sku=deployment_sku,  # Use the SKU for scaling and capacity
            properties=deployment_properties
        )

        # Begin the deployment creation or update
        poller = cognitive_client.deployments.begin_create_or_update(
            resource_group_name=resource_group_name,
            account_name=openai_resource_name,
            deployment_name=deployment_name,
            deployment=deployment
        )

        # Wait for the deployment to complete
        deployment_result = poller.result(timeout=3600)  # Timeout after 1 hour
        print(f"Deployment {deployment_name} completed successfully.")
        return deployment_result

    except HttpResponseError as e:
        print(f"Failed to deploy model: {e.message}")
        raise HTTPException(status_code=500, detail=f"Failed to deploy model: {e.message}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/new_agent")
def new_agent(resource_group:ResourceGroup, db: Session = Depends(get_db)):

    # checking if the agent already exists
    db_item = db.query(Agent).filter(Agent.name == resource_group.name).first()
    if db_item:
        return HTTPException(404, { "message": "Error - agent already exists."})
    else:
        rg_name = f"agent-{resource_group.name}-rg"
        location = resource_group.location

        # Provision the resource group
        rg_result = resource_client.resource_groups.create_or_update(
            rg_name, {"location": location, "tags": {"type": "agent"}}
        )

        db_item = Agent(
            name=rg_name,
            display_name=resource_group.name,
            description=resource_group.description, 
            owner=resource_group.owner, 
            owner_email=resource_group.owner_email,
            model_base=resource_group.model_base,
            location=resource_group.location,
            active=False,
            status='Waiting for approval',
            budget=resource_group.budget
        )
        db.add(db_item)
        db.flush()
        db.refresh(db_item)

        budget_name = f"{rg_name}-budget"
        scope = f"/subscriptions/{subscription_id}/resourceGroups/{rg_name}"
        amount = resource_group.budget
        time_grain = 'Monthly'  # Options: 'Monthly', 'Quarterly', 'Annually'
        start_date = datetime(datetime.now(timezone.utc).year, datetime.now(timezone.utc).month, 1, tzinfo=timezone.utc)
        end_date = datetime(start_date.year + 1, start_date.month, start_date.day)

        # Define notifications (optional)
        notifications = {
            'Actual_GreaterThan_80_Percent': Notification(
                enabled=True,
                operator='GreaterThan',
                threshold=80,
                contact_emails=[resource_group.owner_email],
                threshold_type='Actual'
            )
        }

        # Create the Budget object
        budget = Budget(
            category='Cost',
            amount=amount,
            time_grain=time_grain,
            time_period=BudgetTimePeriod(
                start_date=start_date,
                end_date=end_date
            ),
            notifications=notifications
        )

        # Create or update the budget
        consumption_client.budgets.create_or_update(
            scope=scope,
            budget_name=budget_name,
            parameters=budget
        )

        # Creating the Azure AI Foundry Project
        project_name = f"project-agent{db_item.id}"

        # Initialize the MLClient
        ml_client = MLClient(credentials, subscription_id, rg_name)

        # Define the workspace
        workspace = Workspace(
            name=project_name,
            location=location,
            display_name=resource_group.display_name,
            description=resource_group.description,
        )

        # Create the workspace
        workspace = ml_client.workspaces.begin_create(workspace).result()
        print(f"Provisioned Azure AI Foundry project {workspace.name} in the {workspace.location} region")

        workspace_details = ml_client.workspaces.get(name=project_name)
        workspace_endpoint = workspace_details.discovery_url

        db_item.workspace = workspace_endpoint

        openai_resource_name = f'agent{db_item.id}openai'

        openai_params = Account(
            location=location,
            kind='OpenAI',
            sku=Sku(name='S0'),
            properties={}
        )

        openai_resource = cognitive_client.accounts.begin_create(
            resource_group_name=rg_name,
            account_name=openai_resource_name,
            account=openai_params
        ).result()

        # Retrieve the endpoint from the properties of the OpenAI resource
        openai_endpoint = openai_resource.properties.endpoint

        # Store the OpenAI endpoint and API key in the database
        db_item.openai_endpoint = openai_endpoint

        # Retrieve the API key for the OpenAI resource
        keys = cognitive_client.accounts.list_keys(rg_name, openai_resource_name)
        openai_api_key = keys.key1
        db_item.openai_api_key = openai_api_key

        # Deploy the OpenAI model
        openai_resource_name = f'agent{db_item.id}openai'
        deployment_name = f"gpt-3-deployment-agent{db_item.id}"
        model_name = "gpt-35-turbo"  # Replace with the correct model name

        try:
            deployment_result = deploy_openai_model(
                cognitive_client=cognitive_client,
                resource_group_name=rg_name,
                openai_resource_name=openai_resource_name,
                deployment_name=deployment_name,
                model_name=model_name
            )

            # Store the deployment details in the database
            db_item.deployment_name = deployment_name
            db_item.deployment_status = "Deployed"
            db.commit()

            return {
                "message": f"Provisioned resource group {rg_result.name} and deployed OpenAI model {deployment_name}."
            }

        except HTTPException as e:
            db_item.deployment_status = "Failed"
            db.commit()
            raise e

class ChatRequest(BaseModel):
    agent_id: int
    user_input: str

@app.post("/chat_completion")
async def chat_completion(request: ChatRequest, db: Session = Depends(get_db)):
    # Retrieve the agent from the database
    db_item = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Agent not found.")
    
    # Retrieve the stored OpenAI endpoint, API key, and deployment name from the database
    openai_endpoint = db_item.openai_endpoint
    openai_api_key = db_item.openai_api_key
    deployment_name = f"gpt-3-deployment-agent{db_item.id}" #db_item.deployment_name  # Retrieve the deployment name
    if not openai_endpoint or not openai_api_key or not deployment_name:
        raise HTTPException(status_code=500, detail="OpenAI credentials or deployment not available.")

    # Set up AzureOpenAI client with the retrieved credentials
    client = AzureOpenAI(
        azure_endpoint=openai_endpoint,
        api_key=openai_api_key,
        api_version="2024-02-15-preview"  # Use the correct API version
    )

    try:
        # Create chat completion request using Azure OpenAI
        response = client.chat.completions.create(
            model=deployment_name,  # Use the deployment name from the database
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.user_input},
            ],
        )

        # Extract and return the assistant's reply
        assistant_reply = response.choices[0].message.content
        return {"assistant_reply": assistant_reply}

    except Exception as e:
        # Log the error for debugging
        print(f"Error during chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate chat completion: {str(e)}")

@app.get('/get_agents')
def get_agents(db: Session = Depends(get_db)):
    db_item = db.query(Agent).all()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete('/delete_agent')
def delete_agent(id: int, db: Session = Depends(get_db)):
    db_item = db.query(Agent).filter(Agent.id == id).first()
    if (db_item):
        rg_name = db_item.name

        # deleting resource group
        try:
            # Delete resource group
            resource_client.resource_groups.begin_delete(rg_name)
        except Exception as e:
            print(f"Warning: Failed to delete resource group {rg_name}. Error: {e}")
        
        # deleting the record
        db.delete(db_item)
        db.commit()

        return { "message": f"Record with ID {id} has been deleted."}

    return { "message": "Error - item not found."}

@app.get('/get_agent/{agent_id}')
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Agent).filter(Agent.id == agent_id).first()
    if (db_item):
        resource_group_name = db_item.name
        scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}"

        budget = consumption_client.budgets.get(scope=scope, budget_name=f"{resource_group_name}-budget")

        # Access the current spend amount
        current_spend = budget.current_spend
        if current_spend:
            amount = current_spend.amount
            unit = current_spend.unit
        else:
            current_spend = {'amount': 0}
        
        return { 'message': 'Success', 'agent': db_item, 'budget': db_item.budget, 'current_spend': current_spend}
    
    return HTTPException(404, { 'message': 'Error - agent was not found.' })