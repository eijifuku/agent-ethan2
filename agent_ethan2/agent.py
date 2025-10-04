"""High-level Facade for running AgentEthan2 workflows."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from agent_ethan2.graph import GraphBuilder
from agent_ethan2.ir import normalize_document
from agent_ethan2.loader import YamlLoaderV2
from agent_ethan2.providers import DEFAULT_PROVIDER_FACTORIES
from agent_ethan2.registry import Registry
from agent_ethan2.registry.resolver import ComponentResolver, ProviderResolver, ToolResolver
from agent_ethan2.runtime.scheduler import GraphResult, Scheduler
from agent_ethan2.telemetry import EventBus, TelemetryExporter
from agent_ethan2.telemetry.exporters.console import ConsoleExporter
from agent_ethan2.telemetry.exporters.jsonl import JsonlExporter


class AgentEthan:
    """
    Facade for running AgentEthan2 workflows.
    
    Usage:
        agent = AgentEthan("config.yaml")
        result = await agent.run({"user_prompt": "Hello"})
        
    Or synchronously:
        agent = AgentEthan("config.yaml")
        result = agent.run_sync({"user_prompt": "Hello"})
    """

    def __init__(
        self,
        config_path: Union[str, Path],
        *,
        provider_factories: Optional[Mapping[str, str]] = None,
        tool_factories: Optional[Mapping[str, str]] = None,
        component_factories: Optional[Mapping[str, str]] = None,
        log_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize AgentEthan with a YAML configuration.
        
        Args:
            config_path: Path to YAML v2 configuration file
            provider_factories: Optional mapping of provider type -> factory dotted path
            tool_factories: Optional mapping of tool type -> factory dotted path
            component_factories: Optional mapping of component type -> factory dotted path
            log_path: Optional path for JSONL event logs (default: config_dir/run.jsonl)
        """
        self.config_path = Path(config_path).resolve()
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        # Load and normalize YAML
        loader = YamlLoaderV2()
        document = loader.load_file(self.config_path)
        ir_result = normalize_document(document)
        
        # Extract factory mappings from runtime config if present
        runtime_config = document.get("runtime", {})
        factories_config = runtime_config.get("factories", {})
        
        # Merge provided factories with config factories (provided takes precedence)
        final_provider_factories = {
            **DEFAULT_PROVIDER_FACTORIES,
            **factories_config.get("providers", {}),
            **(provider_factories or {}),
        }
        final_tool_factories = {**factories_config.get("tools", {}), **(tool_factories or {})}
        final_component_factories = {**factories_config.get("components", {}), **(component_factories or {})}
        
        # Create registry
        registry = Registry(
            provider_resolver=ProviderResolver(
                factories=final_provider_factories,
                cache={},
            ),
            tool_resolver=ToolResolver(
                factories=final_tool_factories,
                cache={},
            ),
            component_resolver=ComponentResolver(
                factories=final_component_factories,
                cache={},
            ),
        )
        resolved = registry.materialize(ir_result.ir)
        
        # Store IR for history access
        self.ir = ir_result.ir
        
        # Build graph definition
        self.definition = GraphBuilder().build(ir_result.ir, resolved)
        
        # Setup event bus with exporters from config
        exporters_config = runtime_config.get("exporters", [])
        exporters = self._build_exporters(exporters_config, log_path)
        
        self.event_bus = EventBus(exporters=exporters)
        self.scheduler = Scheduler()
    
    def _build_exporters(
        self,
        exporters_config: list[Mapping[str, Any]],
        default_log_path: Optional[Union[str, Path]],
    ) -> list[TelemetryExporter]:
        """Build exporters from YAML configuration."""
        exporters: list[TelemetryExporter] = []
        
        # If no exporters configured, add default JSONL
        if not exporters_config:
            if default_log_path is None:
                default_log_path = self.config_path.parent / "run.jsonl"
            exporters.append(JsonlExporter(path=Path(default_log_path)))
            return exporters
        
        # Build each configured exporter
        for exporter_cfg in exporters_config:
            exporter_type = exporter_cfg.get("type", "").lower()
            
            if exporter_type == "jsonl":
                path = exporter_cfg.get("path", "run.jsonl")
                exporters.append(JsonlExporter(path=Path(path)))
            
            elif exporter_type == "console":
                color = exporter_cfg.get("color", True)
                verbose = exporter_cfg.get("verbose", False)
                filter_events = exporter_cfg.get("filter_events")
                exporters.append(ConsoleExporter(
                    color=color,
                    verbose=verbose,
                    filter_events=filter_events
                ))
            
            elif exporter_type == "langsmith":
                try:
                    from agent_ethan2.telemetry.exporters.langsmith import LangSmithExporter
                    project_name = exporter_cfg.get("project_name")
                    api_key = exporter_cfg.get("api_key")
                    endpoint = exporter_cfg.get("endpoint")
                    exporters.append(LangSmithExporter(
                        project_name=project_name,
                        api_key=api_key,
                        endpoint=endpoint
                    ))
                except (ImportError, ValueError) as e:
                    import warnings
                    warnings.warn(f"LangSmith exporter not available: {e}")
            
            elif exporter_type == "prometheus":
                try:
                    from agent_ethan2.telemetry.exporters.prometheus import PrometheusExporter
                    port = exporter_cfg.get("port", 9090)
                    exporters.append(PrometheusExporter(port=port))
                except (ImportError, OSError) as e:
                    import warnings
                    warnings.warn(f"Prometheus exporter not available: {e}")
            
            else:
                import warnings
                warnings.warn(f"Unknown exporter type: {exporter_type}")
        
        return exporters

    async def run(
        self,
        inputs: Mapping[str, Any],
        *,
        timeout: Optional[float] = None,
        run_id: Optional[str] = None,
        event_emitter: Optional[EventBus] = None,
    ) -> GraphResult:
        """
        Run the agent asynchronously.
        
        Args:
            inputs: Input values for the graph (e.g. {"user_prompt": "..."})
            timeout: Optional timeout in seconds
            run_id: Optional run ID for tracking
            event_emitter: Optional custom event bus (defaults to built-in)
            
        Returns:
            GraphResult with outputs and metadata
        """
        emitter = event_emitter if event_emitter is not None else self.event_bus
        return await self.scheduler.run(
            self.definition,
            inputs=inputs,
            event_emitter=emitter,
            timeout=timeout,
            run_id=run_id,
        )

    def run_sync(
        self,
        inputs: Mapping[str, Any],
        *,
        timeout: Optional[float] = None,
        run_id: Optional[str] = None,
        event_emitter: Optional[EventBus] = None,
    ) -> GraphResult:
        """
        Run the agent synchronously (blocks until completion).
        
        Args:
            inputs: Input values for the graph (e.g. {"user_prompt": "..."})
            timeout: Optional timeout in seconds
            run_id: Optional run ID for tracking
            event_emitter: Optional custom event bus (defaults to built-in)
            
        Returns:
            GraphResult with outputs and metadata
        """
        return asyncio.run(self.run(inputs, timeout=timeout, run_id=run_id, event_emitter=event_emitter))
