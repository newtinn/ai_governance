from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from io import BytesIO

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.consumption.models import Budget, BudgetTimePeriod, Notification
from azure.mgmt.storage import StorageManagementClient
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Workspace
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import Account, Sku, Deployment, DeploymentModel, DeploymentProperties
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.polling import LROPoller
from azure.core.exceptions import HttpResponseError
from openai import AzureOpenAI

from azure.core.exceptions import ResourceExistsError
from datetime import datetime, timezone, timedelta
import os

from models import Agent, KnowledgeSource, AgentKnowledgeSource, Base
from database import engine, get_db
from sqlalchemy.orm import Session
from schemas import KnowledgeSourceCreate, AgentKnowledgeSourceCreate
from typing import Annotated

from urllib.parse import urlparse
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
user_object_id = os.environ["AZURE_USER_OBJECT_ID"]

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

def deploy_openai_model(cognitive_client, resource_group_name, openai_resource_name, deployment_name, model_name, model_version):
    try:
        # Define the deployment model
        deployment_model = DeploymentModel(
            name=model_name,
            format='OpenAI',
            version=model_version,
            publisher='OpenAI'
        )

        # Define the deployment properties
        deployment_properties = DeploymentProperties(
            model=deployment_model
        )

        # Define the SKU for the deployment
        deployment_sku = Sku(
            name='Standard',
            capacity=1
        )

        # Define the deployment
        deployment = Deployment(
            sku=deployment_sku,
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

import asyncio
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from uuid import uuid4

def assign_storage_role_sync(resource_group_name, storage_account_name, principal_id):
    """
    Assigns 'Storage Blob Data Contributor' role to a given principal.
    :param resource_group_name: Name of the Azure Resource Group
    :param storage_account_name: Name of the Storage Account
    :param principal_id: The Object ID of the user, service principal, or managed identity
    """
    # Define the role definition ID for 'Storage Blob Data Contributor'
    role_definition_id = f"/subscriptions/{subscription_id}/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe"

    # Get the storage account resource ID
    storage_account = storage_client.storage_accounts.get_properties(resource_group_name, storage_account_name)
    storage_account_id = storage_account.id

    # Initialize the Authorization Management Client
    auth_client = AuthorizationManagementClient(credentials, subscription_id)

    # Generate a unique ID for the role assignment
    role_assignment_id = str(uuid4())

    # Create the role assignment parameters
    assignment_params = RoleAssignmentCreateParameters(
        role_definition_id=role_definition_id,
        principal_id=principal_id
    )

    # Assign the role
    auth_client.role_assignments.create(storage_account_id, role_assignment_id, assignment_params)
    print(f"Role 'Storage Blob Data Contributor' assigned to {principal_id} on {storage_account_name}.")

async def assign_storage_role(resource_group_name, storage_account_name, principal_id):
    # Use asyncio.to_thread to run the blocking synchronous function in a separate thread
    await asyncio.to_thread(assign_storage_role_sync, resource_group_name, storage_account_name, principal_id)

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
        model_version = "0125"

        try:
            deployment_result = deploy_openai_model(
                cognitive_client=cognitive_client,
                resource_group_name=rg_name,
                openai_resource_name=openai_resource_name,
                deployment_name=deployment_name,
                model_name=model_name,
                model_version=model_version
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

        # deleting corresponding records
        agent_knowledge_source_item = db.query(AgentKnowledgeSource).filter(AgentKnowledgeSource.agent_id == id).all()
        for item in agent_knowledge_source_item:
            knowledge_source = db.query(KnowledgeSource).filter(KnowledgeSource.id == item.knowledge_id).first()
            if (knowledge_source):
                db.delete(knowledge_source)

            db.delete(item)

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

@app.get('/agent/{agent_id}/get_knowledge_source/{knowledge_source_id}')
def get_knowledge_source(agent_id: int, knowledge_source_id: int, db: Session = Depends(get_db)):
    # Retrieve the agent from the database
    current_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not current_agent:
        raise HTTPException(status_code=404, detail="Agent not found.")
    
    # Retrieve the knowledge source from the database
    knowledge_source = db.query(KnowledgeSource).filter(KnowledgeSource.id == knowledge_source_id).first()
    if not knowledge_source:
        raise HTTPException(status_code=404, detail="Knowledge source not found.")

    try:
        # Get the blob URL from the knowledge source
        blob_url = knowledge_source.source
        
        # Get storage account credentials
        resource_group_name = current_agent.name
        storage_accounts = storage_client.storage_accounts.list_by_resource_group(resource_group_name)
        storage_account = next(storage_accounts, None)
        
        if not storage_account:
            raise HTTPException(
                status_code=404, 
                detail=f"No storage accounts found in resource group '{resource_group_name}'."
            )

        # Get storage key
        keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account.name)
        storage_key = keys.keys[0].value

        # Parse the blob URL to get container and blob names
        parsed_url = urlparse(blob_url)
        # Remove leading '/'
        path_parts = parsed_url.path.lstrip('/').split('/')
        container_name = path_parts[0]
        blob_name = '/'.join(path_parts[1:])

        # Create blob client directly from URL
        blob_client = BlobClient.from_blob_url(
            blob_url=blob_url,
            credential=storage_key
        )

        # Download the blob
        download_stream = blob_client.download_blob()
        file_content = download_stream.readall()

        # Create response headers
        headers = {
            "Content-Disposition": f"attachment; filename={blob_name}",
            "Content-Type": "application/octet-stream"
        }

        # Return streaming response
        return StreamingResponse(
            BytesIO(file_content), 
            media_type="application/octet-stream", 
            headers=headers
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.post('/agent/{agent_id}/add_knowledge_source')
async def add_knowledge_source(agent_id: int, knowledge_source_name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Retrieve the agent from the database
    current_agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not current_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Define the resource group and storage account details
    resource_group_name = current_agent.name
    container_name = f'agent{current_agent.id}-blob'

    storage_accounts = storage_client.storage_accounts.list_by_resource_group(resource_group_name)

    # Get the first storage account
    storage_account = next(storage_accounts, None)
    if not storage_account:
        raise HTTPException(status_code=404, detail=f"No storage accounts found in resource group '{resource_group_name}'.")

    try:
        # Attempt to retrieve the storage account properties
        storage_account = storage_client.storage_accounts.get_properties(
            resource_group_name, storage_account.name
        )
        print(f"Storage account '{storage_account.name}' exists.")
    except:
        print(f"Storage account '{storage_account.name}' does not exist.")

    # Initialize the BlobServiceClient
    account_url = f'https://{storage_account.name}.blob.core.windows.net'

    keys = storage_client.storage_accounts.list_keys(resource_group_name, storage_account.name)
    storage_key = keys.keys[0].value

    blob_service_client = BlobServiceClient(account_url=account_url, credential=storage_key)

    # Get the container client
    container_client = blob_service_client.get_container_client(container_name)

    # Check if the container exists; if not, create it
    if not container_client.exists():
        container_client.create_container()
        print(f"Container '{container_name}' created in storage account '{resource_group_name}'.")

    # Get the blob client
    blob_client = container_client.get_blob_client(file.filename)
    
    file_content = await file.read()

    #await assign_storage_role(resource_group_name, container_name, user_object_id)

    # Upload the file to the blob
    try:
        blob_client.upload_blob(file_content, overwrite=True, blob_type="BlockBlob")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    
    # adding record to database for knowledge source
    db_knowledge_source = KnowledgeSource(name=knowledge_source_name, source=blob_client.url, approved=False)
    db.add(db_knowledge_source)
    db.flush()

    db_knowledge_check = db.query(AgentKnowledgeSource).filter(AgentKnowledgeSource.agent_id == agent_id, AgentKnowledgeSource.knowledge_id == db_knowledge_source.id).first()
    if (db_knowledge_check is None):
        db_agent_knowledge_link = AgentKnowledgeSource(agent_id=agent_id, knowledge_id = db_knowledge_source.id)
        db.add(db_agent_knowledge_link)
    else:
        raise HTTPException(status_code=500, detail='Error uploading file - knowledge source already exists in the database.')
    
    db.commit()

    return {"message": f"File '{file.filename}' uploaded successfully to container '{container_name}'."}

@app.get('/agent/{agent_id}/knowledge_sources')
async def get_knowledge_sources_agent(agent_id: int, db: Session = Depends(get_db)):
    db_item = db.query(AgentKnowledgeSource).filter(AgentKnowledgeSource.agent_id == agent_id).all()
    if (db_item):
        # returning all the knowledge sources
        knowledge_sources = []

        for item in db_item:
            knowledge_source = db.query(KnowledgeSource).filter(KnowledgeSource.id == item.knowledge_id).first()
            if (knowledge_source):
                knowledge_sources.append(knowledge_source)

        return { "message": "Success", "knowledge_sources": knowledge_sources }

    return HTTPException(status_code=404, detail=f'Error - knowledge sources for agent {agent_id} not found.')