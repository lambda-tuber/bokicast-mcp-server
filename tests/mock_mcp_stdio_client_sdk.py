import asyncio
import sys
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ContentBlock
import time

#
# global setting.
#
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(line_buffering=False, write_through=True)

# Target bridge script
BRIDGE_SCRIPT = "bokicast-mcp-server"
CONFIG_YAML_PATH = "C:\\work\\lambda-tuber\\bokicast-mcp-server\\bokicast-mcp-server.yaml"
async def main():

    print(f"Starting connection to Unity via bridge script: {BRIDGE_SCRIPT}")
    print("Unity startup and TCP connection may take several seconds.")

    # 2. Configure server parameters
    server_params = StdioServerParameters(
        command=BRIDGE_SCRIPT,
        args=["-y",
              CONFIG_YAML_PATH],
        env={"PYTHONUTF8": "1"}
    )

    try:
        # 3. Use stdio_client context manager
        async with stdio_client(server_params) as (read_stream, write_stream):
            
            # 4. Create ClientSession
            async with ClientSession(read_stream, write_stream) as session:
                print("Initializing session...")
                
                await session.initialize()
                print("Initialization completed.")

                # ---------------------------------------------------------
                # Get Prompt list
                # ---------------------------------------------------------
                # print("\n--- Prompt List ---")
                # prompts_result = await session.list_prompts()
                
                # for prompt in prompts_result.prompts:
                #     print(f" - {prompt.name}: {prompt.description}")


                # ---------------------------------------------------------
                # Get Prompt
                # ---------------------------------------------------------
                # print("\n--- Prompt Get ---")
                # #help(session)
                # #dir(session)
                # try:
                #     result = await session.get_prompt("prompt_ai_aska")
                #     for msg in result.messages:  # ← 最新 SDK では .messages が正しい
                #         # msg.content は ContentBlock 単体
                #         content = msg.content
                #         if hasattr(content, "text"):
                #             print(f" > {content.text}")
                #         else:
                #             print(f" > {content}")

                #     print("Execution succeeded:")

                # except Exception as e:
                #     print(f"Prompt get execution error: {e}")

                # ---------------------------------------------------------
                # Get tool list
                # ---------------------------------------------------------
                print("\n--- Tool List ---")
                tools_result = await session.list_tools()
                
                for tool in tools_result.tools:
                    print(f" - {tool.name}: {tool.description}")

                # ---------------------------------------------------------
                # Execute tool
                # ---------------------------------------------------------
                journal_data = {
                    "journal_id": "J-004",
                    "debit": [
                        {"account": "仕入", "amount": 1000},
                        {"account": "荷役費", "amount": 500},
                        {"account": "雑費", "amount": 500}
                    ],
                    "credit": [
                        {"account": "買掛金", "amount": 2000}
                    ],
                    "remarks": "仕訳ID004の例"
                }

                print("\n--- Executing 'journal_entry' Tool ---")
                
                try:
                    result = await session.call_tool(
                        "journal_entry",
                        arguments={"journal_data": json.dumps(journal_data)}
                    )

                    # 結果の表示
                    for content in result.content:
                        if isinstance(content, ContentBlock) and hasattr(content, "text"):
                            print(f" > {content.text}")
                        else:
                            print(f" > {content}")

                    print("Tool execution succeeded.")

                except Exception as e:
                    print(f"Tool execution error: {e}")
                    


                print("\n--- Executing 'get_bs' Tool ---")
                
                try:
                    result = await session.call_tool(
                        "get_bs",
                        arguments={}
                    )

                    # 結果の表示
                    for content in result.content:
                        if isinstance(content, ContentBlock) and hasattr(content, "text"):
                            print(f" > {content.text}")
                        else:
                            print(f" > {content}")

                    print("Tool execution succeeded.")

                except Exception as e:
                    print(f"Tool execution error: {e}")

                time.sleep(15)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Unity may not be running or the bridge script may have an issue.")

if __name__ == "__main__":
    asyncio.run(main())
