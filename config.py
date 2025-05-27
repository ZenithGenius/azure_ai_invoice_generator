import os
from dotenv import load_dotenv

load_dotenv()

# Azure AI Foundry Configuration
AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT", "https://jason-m9mz1o12-eastus2.services.ai.azure.com/api/projects/jason-m9mz1o12-eastus2-project")
AGENT_ID = os.getenv("AGENT_ID", "asst_cyFkA3Y2cBHJDZxWd0LiGtYP")

# CosmosDB Configuration
COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT")
COSMOS_KEY = os.getenv("COSMOS_KEY")
COSMOS_DATABASE_NAME = os.getenv("COSMOS_DATABASE_NAME", "InvoiceDB")
COSMOS_CONTAINER_NAME = os.getenv("COSMOS_CONTAINER_NAME", "invoices")

# Azure Search Configuration
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
SEARCH_INDEX_NAME = os.getenv("SEARCH_INDEX_NAME", "invoices-index")

# Azure Storage Configuration
STORAGE_CONNECTION_STRING = os.getenv("STORAGE_CONNECTION_STRING")
STORAGE_CONTAINER_NAME = os.getenv("STORAGE_CONTAINER_NAME", "invoices")

# Company Configuration
COMPANY_NAME = os.getenv("COMPANY_NAME", "Professional Services Inc.")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "123 Business Street, Suite 100, Business City, BC 12345")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+1 (555) 123-4567")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "billing@professionalservices.com")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "www.professionalservices.com")
COMPANY_TAX_ID = os.getenv("COMPANY_TAX_ID", "TAX-123456789") 