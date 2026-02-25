from fastmcp import FastMCP
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.compute import ComputeManagementClient

mcp = FastMCP("AzureSKUExplorer")

def get_default_subscription():
    """Helper to pick the first active subscription from credentials."""
    credential = DefaultAzureCredential()
    sub_client = SubscriptionClient(credential)
    subs = list(sub_client.subscriptions.list())
    if not subs:
        raise Exception("No active subscriptions found for these credentials.")
    return subs[0].subscription_id

@mcp.tool()
def search_azure_skus(location: str = "eastus", filter_str: str = ""):
    """
    Lists all Azure Compute SKUs and their capabilities, filtered by a string.
    
    :param location: The Azure region (e.g., 'eastus', 'westeurope').
    :param filter_str: Search term (e.g., 'v5', 'Gpus', 'Premium'). Case-insensitive.
    """
    try:
        credential = DefaultAzureCredential()
        sub_id = get_default_subscription()
        compute_client = ComputeManagementClient(credential, sub_id)

        # API only supports location filtering server-side
        skus = compute_client.resource_skus.list(filter=f"location eq '{location}'")
        
        results = []
        search_term = filter_str.lower()

        for sku in skus:
            # Flatten capabilities into a dictionary: {"vCPUs": "2", "MemoryGB": "8"}
            capabilities = {cap.name: cap.value for cap in (sku.capabilities or [])}
            
            sku_data = {
                "name": sku.name,
                "resource_type": sku.resource_type,
                "tier": sku.tier,
                "family": sku.family,
                "capabilities": capabilities,
                "restrictions": [r.reason_code for r in (sku.restrictions or [])]
            }

            # Check if filter_str exists in name, family, or any capability key/value
            content_blob = f"{sku.name} {sku.family} {' '.join(capabilities.keys())} {' '.join(capabilities.values())}".lower()
            
            if not filter_str or search_term in content_blob:
                results.append(sku_data)

        return results

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()