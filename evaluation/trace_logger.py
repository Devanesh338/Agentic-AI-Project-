import time
from typing import Dict, Any, List
from langchain_core.callbacks import BaseCallbackHandler

class TraceLogger(BaseCallbackHandler):
    def __init__(self):
        self.trace = {
            "steps": [],
            "tools": [],
            "total_latency": 0.0,
            "llm_calls": 0,
            "start_time": time.time()
        }

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> Any:
        serialized = serialized or {}
        name = kwargs.get("name") or serialized.get("name") or "unknown"
        
        # We only care about LangGraph nodes (which run as chains)
        # Avoid recording the main graph repeatedly if possible, or just record everything and filter later
        if name != "LangGraph":
            self.trace["steps"].append({
                "type": "agent",
                "name": name,
                "start_time": time.time(),
                "inputs": str(inputs)[:500]
            })

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        run_id = kwargs.get("run_id")
        # Find the last step that doesn't have an end time
        for step in reversed(self.trace["steps"]):
            if "end_time" not in step:
                step["end_time"] = time.time()
                step["latency"] = step["end_time"] - step["start_time"]
                step["outputs"] = str(outputs)[:500]
                break

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        self.trace["llm_calls"] += 1

    def finish(self):
        self.trace["total_latency"] = time.time() - self.trace["start_time"]
        return self.trace

def patch_mcp_calls(logger: TraceLogger):
    """Monkey-patch MCP wrappers to intercept latency and success."""
    import mcp_client
    import app.agents.booking_orchestrator as bo
    import functools
    
    def patch_func(module, func_name, tool_name=None):
        orig_func = getattr(module, func_name)
        
        @functools.wraps(orig_func)
        async def wrapper(*args, **kwargs):
            start_t = time.time()
            error = None
            try:
                result = await orig_func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                end_t = time.time()
                logger.trace["tools"].append({
                    "type": "mcp_tool",
                    "tool_name": tool_name or func_name,
                    "arguments": kwargs or args,
                    "success": error is None,
                    "error": error,
                    "latency": end_t - start_t,
                    "timestamp": start_t
                })
        
        setattr(module, func_name, wrapper)
        return orig_func

    # Patch planning MCPs
    orig_tavily = patch_func(mcp_client, "tavily_mcp_search")
    orig_get_airports = patch_func(mcp_client, "get_airports")
    orig_get_airlines = patch_func(mcp_client, "get_airlines")
    orig_weather = patch_func(mcp_client, "weather_mcp_search")
    orig_forecast = patch_func(mcp_client, "forecast_mcp_search")
    
    # Patch booking MCP
    orig_booking_mcp = getattr(bo, "run_booking_mcp_tool")
    @functools.wraps(orig_booking_mcp)
    async def wrapper_booking(tool_name: str, arguments: dict):
        start_t = time.time()
        error = None
        result = None
        try:
            result = await orig_booking_mcp(tool_name, arguments)
            # booking MCP returns JSON strings with 'error' keys sometimes
            if isinstance(result, str) and '"error"' in result:
                import json
                try:
                    parsed = json.loads(result)
                    if "error" in parsed:
                        error = parsed["error"]
                except:
                    pass
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            end_t = time.time()
            logger.trace["tools"].append({
                "type": "mcp_tool",
                "tool_name": tool_name,
                "arguments": arguments,
                "success": error is None,
                "error": error,
                "latency": end_t - start_t,
                "timestamp": start_t
            })
    setattr(bo, "run_booking_mcp_tool", wrapper_booking)

    return {
        "mcp_client.tavily_mcp_search": orig_tavily,
        "mcp_client.get_airports": orig_get_airports,
        "mcp_client.get_airlines": orig_get_airlines,
        "mcp_client.weather_mcp_search": orig_weather,
        "mcp_client.forecast_mcp_search": orig_forecast,
        "app.agents.booking_orchestrator.run_booking_mcp_tool": orig_booking_mcp
    }

def unpatch_mcp_calls(originals: dict):
    import mcp_client
    import app.agents.booking_orchestrator as bo
    setattr(mcp_client, "tavily_mcp_search", originals["mcp_client.tavily_mcp_search"])
    setattr(mcp_client, "get_airports", originals["mcp_client.get_airports"])
    setattr(mcp_client, "get_airlines", originals["mcp_client.get_airlines"])
    setattr(mcp_client, "weather_mcp_search", originals["mcp_client.weather_mcp_search"])
    setattr(mcp_client, "forecast_mcp_search", originals["mcp_client.forecast_mcp_search"])
    setattr(bo, "run_booking_mcp_tool", originals["app.agents.booking_orchestrator.run_booking_mcp_tool"])
