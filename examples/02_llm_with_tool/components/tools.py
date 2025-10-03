"""Tools for Example 02: Calculator."""

from __future__ import annotations

import operator
from typing import Any, Mapping


def calculator_tool_factory(tool, provider_instance):
    """
    Create a simple calculator tool.
    
    Supports basic arithmetic operations: +, -, *, /
    """
    
    async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Execute calculator operation.
        
        Expected inputs:
            operation: str - one of "add", "subtract", "multiply", "divide"
            a: float - first operand
            b: float - second operand
        
        Returns:
            result: float - calculation result
            expression: str - formatted expression (e.g., "10 + 5 = 15")
        """
        operation = inputs.get("operation", "")
        a = float(inputs.get("a", 0))
        b = float(inputs.get("b", 0))
        
        ops = {
            "add": (operator.add, "+"),
            "subtract": (operator.sub, "-"),
            "multiply": (operator.mul, "*"),
            "divide": (operator.truediv, "/"),
        }
        
        if operation not in ops:
            return {
                "result": None,
                "expression": f"Unknown operation: {operation}",
                "error": f"Supported operations: {', '.join(ops.keys())}",
            }
        
        op_func, op_symbol = ops[operation]
        
        try:
            result = op_func(a, b)
            expression = f"{a} {op_symbol} {b} = {result}"
            return {
                "result": result,
                "expression": expression,
            }
        except ZeroDivisionError:
            return {
                "result": None,
                "expression": f"{a} / {b} = undefined",
                "error": "Division by zero",
            }
        except Exception as e:
            return {
                "result": None,
                "expression": f"{a} {op_symbol} {b} = error",
                "error": str(e),
            }
    
    return call

