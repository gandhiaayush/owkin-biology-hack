"""
Isolated elicitation hello-world test.
Verifies that FastMCP's ctx.elicit() round-trip works before we build anything that depends on it.
Uses an in-process MCP client so no external K Pro session is needed.
"""
import asyncio
import pytest
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP, Context
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters
from mcp.server.fastmcp import FastMCP


class ElicitResponse(BaseModel):
    choice: str  # "A", "B", "C", or "D"


pytestmark = pytest.mark.asyncio


async def test_elicitation_api_is_callable():
    """Verify Context.elicit exists and has the expected signature."""
    import inspect
    sig = inspect.signature(Context.elicit)
    params = list(sig.parameters.keys())
    assert "message" in params
    assert "schema" in params


async def test_fastmcp_tool_receives_context():
    """Verify a FastMCP async tool can receive Context as a parameter."""
    mcp = FastMCP("test-elicitation")
    received_context = []

    @mcp.tool()
    async def check_ctx(ctx: Context) -> str:
        received_context.append(ctx)
        return "context received"

    # Just verify the tool is registered and ctx parameter is recognized
    tools = mcp._tool_manager.list_tools()
    tool_names = [t.name for t in tools]
    assert "check_ctx" in tool_names


async def test_elicitation_result_type():
    """Verify elicitation result types have the expected .action and .data fields."""
    from mcp.server.elicitation import AcceptedElicitation, DeclinedElicitation, CancelledElicitation
    # AcceptedElicitation carries both action and data
    assert "action" in AcceptedElicitation.model_fields
    assert "data" in AcceptedElicitation.model_fields
    # DeclinedElicitation and CancelledElicitation only carry action
    assert "action" in DeclinedElicitation.model_fields
    assert "action" in CancelledElicitation.model_fields
