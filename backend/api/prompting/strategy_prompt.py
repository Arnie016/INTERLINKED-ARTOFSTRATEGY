from typing import Dict, List


def build_prompt(query: str, graph_summary: str, exa_snippets: List[Dict[str, str]]) -> str:
    links_text = "\n".join([f"- {x.get('title','')}: {x.get('url','')}\n  {x.get('snippet','')}" for x in exa_snippets])
    return (
        "You are a strategy advisor. Use the ORGANIZATIONAL GRAPH CONTEXT and optional WEB EVIDENCE to answer. "
        "Be brief, precise, quantify targets where possible, and show tradeoffs. "
        "Output must be exactly two XML sections: <strategic_analysis/> and <action_plan/>.\n\n"
        f"USER QUERY:\n{query}\n\n"
        f"ORGANIZATIONAL GRAPH CONTEXT (<=25 nodes):\n{graph_summary}\n\n"
        + (f"WEB EVIDENCE (Top sources):\n{links_text}\n\n" if links_text else "")
        + "Constraints:\n"
        "- Keep total answer <= 600 tokens.\n"
        "- Analysis must discuss risks/alternatives and explicit tradeoffs.\n"
        "- Plan must include owners, timelines, budgets, and measurable targets.\n"
        "- Do not include any other sections beyond the two XML blocks.\n\n"
        "<strategic_analysis>\n"
        "[Concise assessment grounded in graph context and evidence. Mention tradeoffs.]\n"
        "</strategic_analysis>\n"
        "<action_plan>\n"
        "[Bulleted plan with owners, timelines, budgets, KPIs/targets. Quantify.]\n"
        "</action_plan>\n"
    )


