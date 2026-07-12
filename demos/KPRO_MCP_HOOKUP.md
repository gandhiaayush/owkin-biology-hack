# How to hook Discordance MCP into K Pro

Person C ownership: get tools visible in a live session and run baseline vs augmented.  
Person B ownership: ship the MCP server that returns `demos/mocks/or51e2-query.json` shape.

---

## Mental model (important)

```text
YOU build:     Discordance MCP server  (query_or_graph, …)
               ↓  MCP (HTTP preferred for demo)
K Pro / Claude acts as:  MCP client / orchestrator
               ↓  tool calls during a chat
Researcher:    asks the frozen OR51E2 question
```

Owkin’s public docs say K Pro connects to customer tooling **as MCP servers** (not bespoke plugins).  
Winning hackathon tools are also framed as “integrable into K Pro.”

What is **fully documented** today is the reverse direction people confuse with this:
- Claude ← custom connector ← `https://mcp.k.owkin.com/mcp` (Owkin Pathology Explorer)

For **your** server → into a live AI-scientist session, use the playbook below. Confirm the exact K Pro UI control with organizers at kickoff — it may be a Connectors / MCP settings panel that isn’t in the public docs yet.

---

## Step 0 — Prerequisites

- [ ] Person B has a working MCP server locally (`query_or_graph` returns the mock JSON shape)
- [ ] Team has K Pro access (`https://k.owkin.com`)
- [ ] You can expose an **HTTPS** URL to the server (tunnel or cloud host)
- [ ] Frozen question ready (see `PERSON_C_RUNBOOK.md`)

---

## Step 1 — Build / run the MCP server (Person B)

Minimal FastMCP sketch (Python):

```bash
pip install fastmcp
```

```python
# server.py
from fastmcp import FastMCP
import json
from pathlib import Path

mcp = FastMCP("discordance")
GRAPH = json.loads(Path("demos/mocks/or51e2-query.json").read_text())

@mcp.tool()
def query_or_graph(question: str, cancer: str = "prostate", receptor: str = "OR51E2") -> dict:
    """Query the Discordance OR evidence graph. Returns weighted evidence, tensions, and adjudication."""
    # Tonight: return seeded OR51E2 payload.
    # Later: filter/search real graph by question entities.
    out = dict(GRAPH)
    out["query"] = {**GRAPH["query"], "text": question, "cancer": cancer}
    return out

if __name__ == "__main__":
    # HTTP transport so K Pro / Claude can add a remote connector URL
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

Local check:

```bash
npx -y @modelcontextprotocol/inspector http://127.0.0.1:8000/mcp
```

You should see `query_or_graph` listed.

---

## Step 2 — Make it reachable over HTTPS

K Pro / Claude custom connectors want a **public HTTPS** MCP endpoint, not `localhost`.

Fast options for the hackathon:

```bash
# Option A — Cloudflare quick tunnel
cloudflared tunnel --url http://127.0.0.1:8000

# Option B — ngrok
ngrok http 8000
```

You need a URL that looks like:

```text
https://<something>/mcp
```

Keep that process alive during the demo.

---

## Step 3 — Connect the client

### Primary path — Claude + custom MCP connector (confirmed approach)

We are using **Claude.ai + Discordance MCP** as the augmented path.

1. Claude.ai → **Settings → Connectors → Add custom connector**  
   (Team plan: Admin settings → Connectors)  
2. Name: `Discordance`  
3. URL: `https://<your-tunnel>/mcp`  
4. Leave OAuth client id/secret empty  
5. **Connect**, approve, confirm `query_or_graph` and other tools appear  

This is the same connector pattern Owkin uses for their own Pathology Explorer MCP — identical UI, just our server URL.

Refs:
- https://docs.owkin.com/connect-and-integrate/pathology-explorer-mcp-ai-powered-tissue-analysis/getting-started  
- https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp  

### Fallback — Local stdio (dev / debugging only)

Claude Desktop `mcp.json`:

```json
{
  "mcpServers": {
    "discordance": {
      "command": "python",
      "args": ["server.py"]
    }
  }
}
```

### K Pro connector (if organizers enable it)

If Owkin enables custom remote MCP connectors in K Pro during the hackathon, the same HTTPS tunnel URL works — paste it into Settings → Connectors / Integrations. No code change needed; the server already runs in HTTP mode.

---

## Step 4 — Verify in-session

Paste:

```text
Using the Discordance tools only, call query_or_graph for:
Does activating OR51E2 / PSGR suppress or promote prostate cancer phenotypes?
Return tensions and adjudication; do not merge opposing claims.
```

Pass if:
- [ ] Tool call to `query_or_graph` happens  
- [ ] Response shows Neuhaus/Pronin vs Sanz/Rodriguez  
- [ ] `needs_judgment: true` (or elicitation prompt) appears  
- [ ] You can open the tension map alongside and narrate  

---

## Step 5 — Demo choreography (Person C)

1. **Tab 1 — Baseline:** plain Claude (no Discordance connector), saved answer in `demos/mocks/baseline-kpro.txt`  
2. **Tab 2 — Augmented:** Claude.ai with Discordance connector active — same question, tool call visible  
3. **Tab 3 — Tension map:** `demos/or51e2-tension-map.html`  
4. If elicitation unsupported by Claude: use `needs_judgment` options in the tool result and have the “researcher” reply with an option id  

---

## Elicitation note

MCP elicitation (`elicitation/create`) only works if the **client** declares support.  
K Pro may not support it yet.

**Ship both:**
1. Try real elicitation in the tool when deadlock  
2. Always also return `adjudication.needs_judgment` + options (already in the mock)

---

## If K Pro won’t accept custom MCPs yet

Fallback that still tells the story:

| Piece | How |
|---|---|
| Baseline | Real K Pro answer saved to `demos/mocks/baseline-kpro.txt` |
| Augmented | Claude (or Cursor) + your Discordance MCP connector |
| Visual | Local tension map |
| Pitch line | “Built as an MCP server in the shape K Pro already integrates; here’s the live tool call” |

Do **not** block the whole demo on Path A if organizers haven’t enabled custom connectors in the K Pro UI.

---

## Ask organizers / mentors these 4 questions tonight

1. Where in K Pro do we register a **custom remote MCP URL**?  
2. Does it need auth (OAuth / API key / allowlist)?  
3. Is **elicitation** supported in K Pro sessions?  
4. Can we use Claude + Discordance MCP as an accepted augmented path if K Pro connectors aren’t open yet?

---

## Ownership split

| Who | Does |
|---|---|
| **B** | `server.py`, tools, HTTPS tunnel, Inspector green |
| **C** | Add connector in K Pro/Claude, verify tool call, baseline capture, timed run |
| **A** | Keep OR51E2 evidence truth locked so live answers match the map |
