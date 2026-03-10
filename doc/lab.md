# Lab: MCP Server in 60 Lines of Python

In this lab you'll see how easy it is to give an AI agent a brand-new tool. You'll clone a tiny MCP server — about 60 lines of Python — wire it into VS Code, and then ask Copilot plain-English questions that hit live Azure APIs.

---

## Pre-flight Check

Before we start, let's make sure everything is in order. Run each of the following commands in a terminal:

```bash
python3 --version
```

```bash
az account show
```

```bash
git --version
```

You'll need **Python 3.10+**, the **Azure CLI** (logged in), and **Git**. That's all.

---

## 1. Clone & Set Up

The entire MCP server lives in one repo with a single Python file. Clone it and change into the directory:

```bash
git clone https://github.com/edwardsp/azure-sku-mcp.git
cd azure-sku-mcp
```

You don't *have* to use a virtual environment, but it's good practice — it keeps your dependencies isolated and gives VS Code a specific Python path to launch the server with.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you open `requirements.txt` you'll see about 80 packages — that looks like a lot, but they all come from just three top-level dependencies. **FastMCP** is the MCP server framework — it pulls in Pydantic, Starlette, uvicorn, and the MCP protocol library. **azure-identity** handles authentication — that's what lets us reuse `az login` credentials. And **azure-mgmt-compute** is the Azure SDK for querying compute resources like VM SKUs. Everything else in the file is a transitive dependency of those three.

---

## 2. Walk Through the Code

Open `server.py` in the editor. The whole thing is 65 lines — that's all it takes to give an AI agent a brand-new capability.

### The imports and server setup (lines 1–7)

```python
from fastmcp import FastMCP
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

mcp = FastMCP("AzureSKUExplorer")
```

FastMCP is a lightweight framework for building MCP servers. This one line creates the server and gives it a name — that's the name Copilot will see in its tool list.

### The tool function (lines 19–26)

```python
@mcp.tool()
def search_azure_skus(location: str = "eastus", filter_str: str = ""):
    """
    Lists all Azure Compute SKUs and their capabilities, filtered by a string.

    :param location: The Azure region (e.g., 'eastus', 'westeurope').
    :param filter_str: A single substring matched case-insensitively against
        the SKU name, family and all capability keys and values
        (e.g. "NC", "ND", "GPUs").  Note: Use multiple calls for multiple
        filters, as this is a simple substring match and not a full query
        language.
    """
```

This is the key part. The `@mcp.tool()` decorator registers this function as a tool. The function name becomes the tool name. The docstring and type hints tell the AI *what the tool does* and *what parameters it takes*. The better your docstring, the better Copilot knows when and how to call it.

### What it does (lines 27–53)

The body is straightforward — it authenticates to Azure using `DefaultAzureCredential` (which picks up your `az login`), calls the Azure Compute SKUs API for a given region, and filters the results. It returns a plain Python list of dictionaries. FastMCP handles all the JSON serialization and MCP protocol plumbing.

### The entry point (lines 59–60)

```python
if __name__ == "__main__":
    mcp.run()
```

`mcp.run()` starts the server using stdio — that's the transport VS Code uses to talk to MCP servers. When VS Code launches this process, it communicates with it over stdin/stdout. No HTTP server, no ports to configure. FastMCP does support HTTP and WebSocket transports too, but stdio is the simplest for local development and works great with VS Code.

---

## 3. Add to VS Code

Now you need to tell VS Code about the server. VS Code looks for a `.vscode/mcp.json` file in your workspace — it's the simplest way to register MCP servers.

Create the directory:

```bash
mkdir .vscode
```

In VS Code, create a new file `.vscode/mcp.json` and enter the following:

> **TIP:** Get your repo path by running `pwd` in the terminal — use that to replace the paths below.

```jsonc
{
    "servers": {
        "azure-sku-explorer": {
            "command": "<your-repo-path>/.venv/bin/python",
            "args": ["<your-repo-path>/server.py"],
            "env": {}
        }
    }
}
```

> For example, if `pwd` shows `/home/paul/Microsoft/HandsOnLab/azure-sku-mcp`:
>
> ```jsonc
> {
>     "servers": {
>         "azure-sku-explorer": {
>             "command": "/home/paul/Microsoft/HandsOnLab/azure-sku-mcp/.venv/bin/python",
>             "args": ["/home/paul/Microsoft/HandsOnLab/azure-sku-mcp/server.py"],
>             "env": {}
>         }
>     }
> }
> ```

Three things to note: `command` points to the Python *inside your virtual environment* so it has all the packages. `args` is the path to `server.py`. And `env` lets you pass environment variables if needed — you don't need any here because `az login` handles auth. This configuration stays with the project — no need to edit your global settings.

**Save the file**, then press `Ctrl+Shift+P` → **"Developer: Reload Window"**.

After reloading, VS Code picks up the `mcp.json` and starts the server in the background.

---

## 4. Try It Out in Copilot Chat

Open **Copilot Chat** and switch to **Agent mode**.

### Prompt 1 — Basic query

Type the following into the chat:

```
What GPU VM sizes are available in eastus2? Show me their vCPU and memory specs.
```

While it runs, watch what happens — Copilot reads the tool description, decides this question needs Azure SKU data, picks the right region and filter, and calls the tool. The function returns raw JSON; the AI handles all the formatting.

Once results appear, you should see a nicely formatted table. All of this comes from live Azure data, not training data — it's current, real-time information from the Azure API.

### Prompt 2 — Multi-call reasoning

Type the following:

```
What is the cache disk size on NC40ads_H100_v5 and ND96isr_H100_v5 SKUs in eastus?
```

This is where it gets interesting — notice Copilot makes *two* parallel tool calls, one for NC and one for ND. It decomposes a single question into multiple API calls on its own, then converts bytes to gigabytes and formats the results into tables.

No formatting code, no unit conversion code, and no logic to split the query was written. The MCP tool just returns raw data — the AI does the thinking.

---

## Wrap-Up

That's MCP in practice: 60 lines of Python, one decorated function, and you've given an AI agent the ability to query live Azure infrastructure data. The pattern is always the same — write a function, decorate it with `@mcp.tool()`, return data, and the AI figures out when and how to use it.
