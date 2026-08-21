import os
import ipaddress
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

load_dotenv()  # Pulls DEVICE_USERNAME / DEVICE_PASSWORD / DEVICE_TYPE from .env

# --- MCP Server object ---
# Registering this starts the "Server" role from the article's 3 MCP roles
# (Host / Client / Server). This process will later respond to
# initialize, tools/list, and tools/call JSON-RPC requests over stdio.
mcp = FastMCP("netmiko-network-server")

CREDS = {
    "device_type": os.getenv("DEVICE_TYPE", "cisco_ios"),
    "username": os.getenv("DEVICE_USERNAME"),
    "password": os.getenv("DEVICE_PASSWORD"),
}


def _run(device_ip: str, command: str) -> str:
    """
    STAGE 5 — Script Execution & Payload Return.
    This is where the MCP Server actually does the work: validates input,
    opens the Netmiko SSH session, runs the command, and returns the raw
    console output back up to whichever @mcp.tool() called it.
    """
    # Input validation — prevents malformed IPs ("10.1.1", "100") from
    # ever reaching Netmiko/Paramiko as a raw socket target.
    try:
        ipaddress.ip_address(device_ip)
    except ValueError:
        return f"ERROR: '{device_ip}' is not a valid IP address."

    try:
        conn = ConnectHandler(host=device_ip, **CREDS)
        output = conn.send_command(command)
        conn.disconnect()
        return output                      # <-- returned as the JSON-RPC "result"
    except NetmikoTimeoutException:
        return f"ERROR: Device {device_ip} is unreachable (connection timed out)."
    except NetmikoAuthenticationException:
        return f"ERROR: Authentication failed for device {device_ip}."
    except Exception as e:
        return f"ERROR: Unexpected failure connecting to {device_ip}: {e}"


# ---------------------------------------------------------------------
# Each function below is registered as an MCP "tool" the moment the
# @mcp.tool() decorator runs, at Server startup.
# This is also what STAGE 1 (tools/list) will later return to the Client:
# the tool's name, its docstring (used as the "description" field), and
# its type-hinted parameters (auto-converted into a JSON schema).
# ---------------------------------------------------------------------

@mcp.tool()
def netmiko_ping(device_ip: str, target_ip: str) -> str:
    """Ping target_ip from device_ip to check Layer 3 reachability."""
    return _run(device_ip, f"ping {target_ip}")


@mcp.tool()
def netmiko_traceroute(device_ip: str, target_ip: str) -> str:
    """Traceroute to target_ip from device_ip to show the hop-by-hop path."""
    return _run(device_ip, f"traceroute {target_ip}", read_timeout=60)


@mcp.tool()
def netmiko_show_route(device_ip: str, destination: str = "") -> str:
    """Show the routing table on device_ip, optionally filtered to a destination network."""
    cmd = f"show ip route {destination}".strip()
    return _run(device_ip, cmd)


@mcp.tool()
def netmiko_show_interfaces(device_ip: str, interface: str = "") -> str:
    """Show interface status/details on device_ip, optionally for one specific interface."""
    cmd = f"show ip interface brief {interface}".strip()
    return _run(device_ip, cmd)


if __name__ == "__main__":
    # STAGE 1 (server-side half) — the moment this line runs, the Server
    # starts listening on stdin/stdout for JSON-RPC messages: initialize,
    # tools/list, and tools/call. It stays alive as a subprocess for the
    # entire lifetime of the Client session.
    mcp.run(transport="stdio")