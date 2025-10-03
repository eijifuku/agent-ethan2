"""LLM component with lifecycle hooks."""

from __future__ import annotations

import time
from typing import Any, Mapping, Optional


class LoggingLLM:
    """LLM component with before/after hooks for logging."""
    
    def __init__(self, client: Any, model: str):
        self.client = client
        self.model = model
    
    async def before_execute(
        self,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Mapping[str, Any]]:
        """Log before execution and add timestamp."""
        node_id = ctx.get('node_id', 'unknown')
        prompt = inputs.get('prompt', '')
        
        print(f"\n{'='*60}")
        print(f"[{node_id}] 🚀 BEFORE EXECUTE")
        print(f"{'='*60}")
        print(f"  Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"  Model: {self.model}")
        
        # Add timestamp to inputs
        return {**inputs, "_started_at": time.time()}
    
    async def after_execute(
        self,
        result: Any,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Any]:
        """Log after execution and add metadata."""
        node_id = ctx.get('node_id', 'unknown')
        started_at = inputs.get('_started_at', time.time())
        duration = time.time() - started_at
        
        text = result.get('choices', [{}])[0].get('text', '') if isinstance(result, dict) else str(result)
        
        print(f"\n{'='*60}")
        print(f"[{node_id}] ✅ AFTER EXECUTE")
        print(f"{'='*60}")
        print(f"  Response: {text[:100]}{'...' if len(text) > 100 else ''}")
        print(f"  Duration: {duration:.3f}s")
        
        # Add metadata to result
        if isinstance(result, dict):
            return {
                **result,
                "_metadata": {
                    "node_id": node_id,
                    "duration": duration,
                    "model": self.model
                }
            }
        return result
    
    async def on_error(
        self,
        error: Exception,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> None:
        """Log errors and send alerts."""
        node_id = ctx.get('node_id', 'unknown')
        
        print(f"\n{'='*60}")
        print(f"[{node_id}] ❌ ERROR")
        print(f"{'='*60}")
        print(f"  Error: {type(error).__name__}: {error}")
        print(f"  Inputs: {inputs}")
        
        # In production: send to monitoring/alerting system
        # await send_alert(f"LLM component {node_id} failed: {error}")
    
    async def __call__(
        self,
        state: Mapping[str, Any],
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        """Main execution logic."""
        import asyncio
        
        prompt = inputs.get('prompt', '')
        loop = asyncio.get_running_loop()
        
        def _invoke():
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            usage = response.usage
            usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else {}
            text = response.choices[0].message.content if response.choices else ""
            return {
                "choices": [{"text": text}],
                "usage": usage_dict,
            }
        
        return await loop.run_in_executor(None, _invoke)


class CachedComponent:
    """Component with caching using hooks."""
    
    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0
    
    async def before_execute(
        self,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Mapping[str, Any]]:
        """Check cache before execution."""
        import json
        
        cache_key = json.dumps(inputs, sort_keys=True)
        
        if cache_key in self.cache:
            self.hits += 1
            print(f"\n💾 Cache HIT ({self.hits} hits, {self.misses} misses)")
            # Store cached result in context
            ctx['_cached_result'] = self.cache[cache_key]
        else:
            self.misses += 1
            print(f"\n🔍 Cache MISS ({self.hits} hits, {self.misses} misses)")
        
        return None
    
    async def after_execute(
        self,
        result: Any,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Any]:
        """Store result in cache."""
        import json
        
        # Don't cache if we used a cached result
        if '_cached_result' not in ctx:
            cache_key = json.dumps(inputs, sort_keys=True)
            self.cache[cache_key] = result
            print(f"💾 Cached result for key: {cache_key[:50]}...")
        
        return None
    
    async def __call__(
        self,
        state: Mapping[str, Any],
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        """Main logic - skip if cached."""
        # Return cached result if available
        if '_cached_result' in ctx:
            return ctx['_cached_result']
        
        # Simulate expensive computation
        import asyncio
        await asyncio.sleep(0.1)
        
        value = inputs.get('value', '')
        return {"result": value.upper(), "length": len(value)}

