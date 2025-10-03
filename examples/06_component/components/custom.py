"""Custom component implementations."""

from __future__ import annotations

import json
from typing import Any, Mapping


async def text_analyzer(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Analyze text and extract statistics.
    
    Expected inputs:
        text: str - the text to analyze
    
    Returns:
        word_count: int - number of words
        char_count: int - number of characters
        line_count: int - number of lines
        unique_words: int - number of unique words
        avg_word_length: float - average word length
    """
    text = inputs.get("text", "")
    
    lines = text.split('\n')
    words = text.split()
    chars = len(text)
    unique = len(set(word.lower().strip('.,!?;:') for word in words))
    avg_len = sum(len(word) for word in words) / len(words) if words else 0.0
    
    return {
        "word_count": len(words),
        "char_count": chars,
        "line_count": len(lines),
        "unique_words": unique,
        "avg_word_length": round(avg_len, 2),
    }


async def json_transformer(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Transform JSON data according to rules.
    
    Expected inputs:
        data: dict - the data to transform
        operation: str - operation to perform (uppercase_keys, lowercase_values, filter_nulls)
    
    Returns:
        result: dict - transformed data
        operation_applied: str - the operation that was applied
    """
    data = inputs.get("data", {})
    operation = inputs.get("operation", "uppercase_keys")
    
    if not isinstance(data, dict):
        return {
            "result": data,
            "operation_applied": "none",
            "error": "Input is not a dictionary",
        }
    
    result = data.copy()
    
    if operation == "uppercase_keys":
        result = {k.upper(): v for k, v in data.items()}
    elif operation == "lowercase_values":
        result = {k: (v.lower() if isinstance(v, str) else v) for k, v in data.items()}
    elif operation == "filter_nulls":
        result = {k: v for k, v in data.items() if v is not None}
    
    return {
        "result": result,
        "operation_applied": operation,
    }


async def data_aggregator(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Aggregate data from multiple sources.
    
    Expected inputs:
        numbers: list - list of numbers to aggregate
    
    Returns:
        sum: float - sum of numbers
        avg: float - average of numbers
        min: float - minimum value
        max: float - maximum value
        count: int - count of numbers
    """
    numbers = inputs.get("numbers", [])
    
    if not numbers:
        return {
            "sum": 0.0,
            "avg": 0.0,
            "min": 0.0,
            "max": 0.0,
            "count": 0,
        }
    
    return {
        "sum": sum(numbers),
        "avg": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "count": len(numbers),
    }

