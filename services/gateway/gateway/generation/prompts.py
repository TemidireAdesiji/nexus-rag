"""Prompt templates for the generation pipeline."""

ANSWER_TEMPLATE: str = (
    "You are NexusRAG, an intelligent research "
    "assistant. Use the provided context to answer "
    "the question accurately and concisely.\n\n"
    "## Retrieved Context\n"
    "{context}\n\n"
    "## API Intelligence\n"
    "{api_context}\n\n"
    "## Conversation History\n"
    "{chat_history}\n\n"
    "## Question\n"
    "{question}\n\n"
    "## Instructions\n"
    "- Synthesise information from all sources.\n"
    "- Cite specific details when available.\n"
    "- If the context is insufficient, state that "
    "clearly.\n"
    "- Keep the response focused and well-structured."
    "\n\nAnswer:"
)

MULTI_QUERY_TEMPLATE: str = (
    "You are a research query specialist. "
    "Generate three alternative versions of the "
    "following question to improve document "
    "retrieval. Each version should approach "
    "the topic from a different angle.\n\n"
    "Original question: {question}\n\n"
    "Provide exactly three alternative queries, "
    "one per line, with no numbering or bullets:"
)

DECOMPOSITION_TEMPLATE: str = (
    "You are a research analyst. Break the "
    "following complex question into simpler "
    "sub-questions that can be answered "
    "independently.\n\n"
    "Complex question: {question}\n\n"
    "Provide up to four sub-questions, "
    "one per line, with no numbering or bullets:"
)

TOOL_PLANNING_TEMPLATE: str = (
    "You are a tool-selection specialist. "
    "Given a user question, available tools, and "
    "any detected entities, decide which tools "
    "to call and with what parameters.\n\n"
    "Available tools: {tool_names}\n\n"
    "Detected entities:\n"
    "- People: {people}\n"
    "- Organisations: {organisations}\n"
    "- Industries: {industries}\n\n"
    "Question: {question}\n\n"
    "Respond with a JSON array of objects, each "
    "having keys: tool, params (object), "
    "rationale (string).\n"
    "If no tools are needed, return []."
)
