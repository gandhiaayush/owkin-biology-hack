# Query mock contract (Person B ↔ Person C)

## File
- `or51e2-query.json` — source of truth for the demo query response
- `or51e2-query.embed.js` — same payload as `window.DISCORDANCE_QUERY` for `file://` demos

## Tool name (proposed)
`query_or_graph`

### Input
```json
{
  "question": "string",
  "cancer": "prostate",
  "receptor": "OR51E2"
}
```

### Output
Match the top-level keys in `or51e2-query.json`:
- `consensus`, `tumor_suppressive`, `tumor_promoting`, `exploratory`
- `tensions`, `scores`, `rules`
- `adjudication.needs_judgment` + `adjudication.elicitation.options`

## Swap path
1. Person C demos read `window.DISCORDANCE_QUERY` (mock)
2. When MCP is live, K Pro tool result should be the same shape
3. Person C can paste live JSON over the mock without UI rewrites

## Elicitation fallback
If client has no elicitation support, still return `adjudication` and wait for the user to pick an option id in the next turn.
