"""Tool implementations for Example 07."""

from __future__ import annotations

from typing import Any, Mapping


async def web_search_tool(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Simulate a web search tool.
    
    Expected inputs:
        query: str - the search query
    
    Returns:
        results: list - list of search results
        count: int - number of results
    """
    query = inputs.get("query", "")
    
    # Simulate search results (in real implementation, use actual search API)
    results = [
        {"title": f"Result 1 for '{query}'", "snippet": "This is a relevant search result..."},
        {"title": f"Result 2 for '{query}'", "snippet": "Another interesting finding..."},
        {"title": f"Result 3 for '{query}'", "snippet": "More information about the topic..."},
    ]
    
    return {
        "results": results,
        "count": len(results),
        "query": query,
    }


async def calculator_tool(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Perform mathematical calculations.
    
    Expected inputs:
        operation: str - add, subtract, multiply, divide
        a: float - first operand
        b: float - second operand
    
    Returns:
        result: float - calculation result
        expression: str - the expression that was evaluated
    """
    operation = inputs.get("operation", "add")
    a = float(inputs.get("a", 0))
    b = float(inputs.get("b", 0))
    
    if operation == "add":
        result = a + b
        expr = f"{a} + {b}"
    elif operation == "subtract":
        result = a - b
        expr = f"{a} - {b}"
    elif operation == "multiply":
        result = a * b
        expr = f"{a} * {b}"
    elif operation == "divide":
        if b == 0:
            return {"error": "Division by zero", "result": None}
        result = a / b
        expr = f"{a} / {b}"
    else:
        return {"error": f"Unknown operation: {operation}", "result": None}
    
    return {
        "result": result,
        "expression": expr,
    }


async def data_validator(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Validate input data.
    
    Expected inputs:
        data: dict - data to validate
        required_fields: list - list of required field names
    
    Returns:
        valid: bool - whether data is valid
        missing_fields: list - list of missing required fields
        message: str - validation message
    """
    data = inputs.get("data", {})
    required_fields = inputs.get("required_fields", [])
    
    if not isinstance(data, dict):
        return {
            "valid": False,
            "missing_fields": [],
            "message": "Data must be a dictionary",
        }
    
    missing = [field for field in required_fields if field not in data]
    
    if missing:
        return {
            "valid": False,
            "missing_fields": missing,
            "message": f"Missing required fields: {', '.join(missing)}",
        }
    
    return {
        "valid": True,
        "missing_fields": [],
        "message": "All required fields present",
    }

