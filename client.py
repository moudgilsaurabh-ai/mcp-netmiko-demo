import asyncio
import json
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "llama3.1"


async def main():
    server = StdioServerParameters(command="python", args=["server.py"])

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()                              # Stage 1
            tools = (await session.list_tools()).tools

            ollama_tools = [{
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema,
                },
            } for t in tools]

            # --- User prompt now taken interactively ---
            user_prompt = input("Enter your networking request: ").strip()
            if not user_prompt:
                print("No input provided. Exiting.")
                return

            messages = [{"role": "user", "content": user_prompt}]

            resp = ollama.chat(model=MODEL, messages=messages, tools=ollama_tools)  # Stage 2 -> 3
            msg = resp["message"]
            messages.append(msg)

            if not msg.get("tool_calls"):
                print("\nModel responded without calling a tool:\n", msg.get("content"))
                return

            for call in msg.get("tool_calls", []):
                args = call["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)

                print(f"-> Calling tool: {call['function']['name']} with {args}")
                result = await session.call_tool(call["function"]["name"], arguments=args)  # Stage 4 -> 5
                messages.append({"role": "tool", "content": result.content[0].text})

            final = ollama.chat(model=MODEL, messages=messages)      # Stage 6
            print("\nFinal answer:\n", final["message"]["content"])


if __name__ == "__main__":
    asyncio.run(main())