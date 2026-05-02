from agent.state import AgentState

def router(state: AgentState) -> str:
    """
    Determines the next path in the graph based on the planner's classification.
    """
    next_action = state.get("next_action", "end")
    
    if next_action == "browser":
        return "browser_executor"
    elif next_action == "os":
        return "os_executor"
    else:
        return "end"
