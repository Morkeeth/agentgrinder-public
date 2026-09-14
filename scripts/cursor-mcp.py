"""Launch the repository MCP server independently of the client working directory."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agentgrinder.mcp_server import main

if __name__ == "__main__":
    main()
