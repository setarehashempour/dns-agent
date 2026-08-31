import os
import sys
import json
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from agent_config import SYSTEM_PROMPT, TOOLS_SCHEMA
from tools import check_dns_records, check_port_status, detect_cdn

console = Console()

AVAILABLE_TOOLS = {
    "check_dns_records": check_dns_records,
    "check_port_status": check_port_status,
    "detect_cdn": detect_cdn
}

def run_dns_agent(domain: str):
    api_key = os.getenv("AVALAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] AVALAI_API_KEY is not set.")
        console.print("Set it using: export AVALAI_API_KEY='your_key'")
        return

    # اتصال به سرورهای سرویس ایرانی AvalAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.avalai.ir/v1"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Troubleshoot and diagnose network/DNS issues for domain: {domain}"}
    ]

    console.print(Panel(f"[bold cyan]Starting Troubleshooting for:[/bold cyan] {domain}", title="DNS Agent (AvalAI - GPT-4o-mini)"))

    # استفاده از مدل gpt-4o-mini با پشتیبانی کامل از Tool Calling بدون فیلتر و محدودیت
    MODEL_NAME = "gpt-4o-mini"

    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )
        except Exception as err:
            console.print(f"[bold red]API Error:[/bold red] {err}")
            break

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                console.print(f"🤖 [bold yellow]Agent Decision:[/bold yellow] Executing tool [green]{function_name}[/green] with args {function_args}")

                tool_function = AVAILABLE_TOOLS.get(function_name)
                if tool_function:
                    tool_output = tool_function(**function_args)
                    console.print(f"⚙️ [bold blue]Tool Output:[/bold blue] {tool_output}\n")
                else:
                    tool_output = {"error": f"Tool {function_name} not found."}

                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(tool_output)
                })
        else:
            console.print(Panel(response_message.content, title=f"[bold green]Final Diagnostic Report ({MODEL_NAME})[/bold green]", border_style="green"))
            break

if __name__ == "__main__":
    target_domain = sys.argv[1] if len(sys.argv) > 1 else input("Enter domain to troubleshoot (e.g., google.com): ")
    run_dns_agent(target_domain.strip())
