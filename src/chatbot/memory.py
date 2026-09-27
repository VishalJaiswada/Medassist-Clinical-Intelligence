"""Stateful conversation via LangGraph: history is kept per thread so
follow-up questions ('what about his labs?') work without repeating the ID."""
from src import config


def build_chat_app(llm):
    from langchain_core.messages import SystemMessage
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import START, MessagesState, StateGraph

    workflow = StateGraph(state_schema=MessagesState)

    def call_model(state: MessagesState):
        messages = [SystemMessage(content=config.SYSTEM_PROMPT)] + state["messages"]
        return {"messages": llm.invoke(messages)}

    workflow.add_node("model", call_model)
    workflow.add_edge(START, "model")
    return workflow.compile(checkpointer=MemorySaver())


class Conversation:
    """Thin wrapper: respond(question, context) -> answer text, with memory."""

    def __init__(self, llm, thread_id: str = "medassist-1"):
        self.app = build_chat_app(llm)
        self.thread = {"configurable": {"thread_id": thread_id}}
        self.last_patient_ids: list[str] = []

    def respond(self, question: str, context: str, instructions: str | None = None) -> str:
        """Answer a question given context. `instructions` optionally overrides
        the task framing for this call only (e.g. the symptom checker)."""
        from langchain_core.messages import HumanMessage

        context_msg = f"Patient record sections:\n{context}"
        if instructions:
            context_msg = f"Task instructions:\n{instructions}\n\n{context_msg}"

        out = self.app.invoke(
            {"messages": [
                HumanMessage(content=f"Question: {question}"),
                HumanMessage(content=context_msg),
            ]},
            self.thread,
        )
        return out["messages"][-1].content

    def reset(self, thread_id: str = "medassist-1"):
        self.thread = {"configurable": {"thread_id": thread_id}}
        self.last_patient_ids = []
