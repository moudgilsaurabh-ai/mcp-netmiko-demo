# MCP + Netmiko Network Diagnostics Demo

A minimal, from-scratch showcase of the **Model Context Protocol (MCP)** using **Netmiko** to run real network diagnostics (ping, traceroute, routing table, interface status) — orchestrated end-to-end by a local **Ollama** LLM. No Claude Desktop, Cursor, or any GUI host application required — everything runs as plain Python scripts, making it suitable for locked-down/restricted machines.

---

## What This Demonstrates

MCP defines three roles:

- **Host** — the application the user interacts with (in this project: `client.py`)
- **Client** — created by the Host, talks to exactly one MCP Server
- **Server** — exposes capabilities/tools (in this project: `server.py`, wrapping Netmiko)

This project also demonstrates the full 6-stage request lifecycle:

| Stage | Description | Where it happens |
|---|---|---|
| 1 | Application Startup — Silent Discovery | `session.initialize()`, `session.list_tools()` |
| 2 | Message Assembly | MCP tool schemas converted into Ollama's function-calling format |
| 3 | LLM Intent & Tool Selection | `ollama.chat()` decides which tool(s) to call |
| 4 | MCP Server Invocation | `session.call_tool()` sends a JSON-RPC `tools/call` over stdio |
| 5 | Script Execution & Payload Return | Netmiko runs the command against the device inside `server.py` |
| 6 | Context Feed-Back & Final Answer | Tool output sent back to the LLM for a plain-English answer |

---

## File Structure
mcp-netmiko-demo/
├── .env # static credentials (never sent to the LLM)
├── .gitignore
├── requirements.txt
├── server.py # MCP Server — exposes 4 Netmiko tools
└── client.py # MCP Client / Host — talks to Ollama + MCP Server

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally
- Network access (SSH) to at least one Cisco IOS/IOS-XE device — or use the [Cisco DevNet Always-On IOS-XE Sandbox](https://developer.cisco.com/site/sandbox/) if you don't have a lab device

---

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS/Linux

2. Install dependencies
pip install -r requirements.txt

requirements.txt:
mcp
netmiko
python-dotenv
ollama

3. Configure credentials

Create a .env file in the project root with following:

DEVICE_USERNAME=admin
DEVICE_PASSWORD=admin123
DEVICE_TYPE=cisco_ios


⚠️ Do not commit .env. It's already listed in .gitignore. Credentials stay in the server's environment and are never passed through the LLM or the MCP protocol messages — the model only ever sees device_ip and command-specific parameters.

4. Pull an Ollama model with tool-calling support

ollama pull llama3.1

Alternatives if llama3.1 isn't suitable: qwen2.5, mistral-nemo.

Confirm Ollama is running:

ollama list


Running the Demo

Do not run server.py directly — it's designed to be spawned as a subprocess by the client and will simply sit blocked waiting for stdio input (this is expected behavior, not a bug, and can be terminated with Ctrl+C).

Run the client instead:

python client.py

Enter your networking request: From device 192.168.1.1, ping 8.8.8.8 and show the route to 8.8.8.8
