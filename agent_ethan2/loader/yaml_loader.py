"""YAML v2 loader and validator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple, Union
import json

import yaml
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaValidationError
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


PointerPath = Tuple[Union[str, int], ...]
Pointer = str
Location = Tuple[int, int]


@dataclass(frozen=True)
class ValidationIssue:
    """Represents a single validation issue surfaced to the caller."""

    code: str
    message: str
    pointer: Pointer
    line: Optional[int]
    column: Optional[int]
    source: Optional[str] = None


class YamlValidationError(ValueError):
    """Raised when the YAML configuration does not satisfy the v2 contract."""

    def __init__(self, issue: ValidationIssue):
        self.issue = issue
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        location = ""
        if self.issue.line is not None and self.issue.column is not None:
            location = f" (line {self.issue.line}, col {self.issue.column})"
        pointer = f" at {self.issue.pointer}" if self.issue.pointer else ""
        source = f" in {self.issue.source}" if self.issue.source else ""
        return f"[{self.issue.code}] {self.issue.message}{pointer}{location}{source}"


class _YamlComposer:
    """Helper to convert a YAML document node into Python objects with locations."""

    def __init__(self, source: str):
        self._source = source
        self._locations: Dict[Pointer, Location] = {}

    @property
    def locations(self) -> Mapping[Pointer, Location]:
        return self._locations

    def compose(self) -> Any:
        try:
            document = yaml.compose(self._source, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            message = getattr(exc, "problem", str(exc)) or "Invalid YAML input"
            (line, column) = self._extract_mark(exc)
            issue = ValidationIssue(
                code="ERR_YAML_PARSE",
                message=message,
                pointer="/",
                line=line,
                column=column,
            )
            raise YamlValidationError(issue) from exc
        if document is None:
            issue = ValidationIssue(
                code="ERR_YAML_EMPTY",
                message="YAML document is empty",
                pointer="/",
                line=None,
                column=None,
            )
            raise YamlValidationError(issue)
        return self._convert(document, ())

    @staticmethod
    def _extract_mark(exc: yaml.YAMLError) -> Tuple[Optional[int], Optional[int]]:
        mark = getattr(exc, "problem_mark", None)
        if mark is None:
            return (None, None)
        return (mark.line + 1, mark.column + 1)

    def _convert(self, node: Node, path: PointerPath) -> Any:
        pointer = _pointer_from_path(path)
        if pointer not in self._locations:
            self._locations[pointer] = (node.start_mark.line + 1, node.start_mark.column + 1)

        if isinstance(node, ScalarNode):
            return self._convert_scalar(node)
        if isinstance(node, SequenceNode):
            values: List[Any] = []
            for idx, child in enumerate(node.value):
                child_path = path + (idx,)
                values.append(self._convert(child, child_path))
            return values
        if isinstance(node, MappingNode):
            mapping: Dict[str, Any] = {}
            for key_node, value_node in node.value:
                key = self._convert_key(key_node)
                child_path = path + (key,)
                if key in mapping:
                    location = (value_node.start_mark.line + 1, value_node.start_mark.column + 1)
                    pointer_child = _pointer_from_path(child_path)
                    self._locations.setdefault(pointer_child, location)
                    issue = ValidationIssue(
                        code="ERR_YAML_DUPLICATE_KEY",
                        message=f"Duplicate key '{key}' encountered",
                        pointer=pointer_child,
                        line=location[0],
                        column=location[1],
                    )
                    raise YamlValidationError(issue)
                self._locations.setdefault(
                    _pointer_from_path(child_path),
                    (value_node.start_mark.line + 1, value_node.start_mark.column + 1),
                )
                mapping[key] = self._convert(value_node, child_path)
            return mapping
        issue = ValidationIssue(
            code="ERR_YAML_NODE_UNSUPPORTED",
            message=f"Unsupported YAML node type: {type(node).__name__}",
            pointer=pointer,
            line=node.start_mark.line + 1,
            column=node.start_mark.column + 1,
        )
        raise YamlValidationError(issue)

    @staticmethod
    def _convert_scalar(node: ScalarNode) -> Any:
        tag = node.tag
        value = node.value
        if tag.endswith(":null"):
            return None
        if tag.endswith(":bool"):
            return value.lower() in {"true", "yes", "on"}
        if tag.endswith(":int"):
            try:
                return int(value)
            except ValueError as exc:
                raise YamlValidationError(
                    ValidationIssue(
                        code="ERR_YAML_SCALAR",
                        message=f"Invalid integer literal '{value}'",
                        pointer="/",
                        line=node.start_mark.line + 1,
                        column=node.start_mark.column + 1,
                    )
                ) from exc
        if tag.endswith(":float"):
            try:
                return float(value)
            except ValueError as exc:
                raise YamlValidationError(
                    ValidationIssue(
                        code="ERR_YAML_SCALAR",
                        message=f"Invalid float literal '{value}'",
                        pointer="/",
                        line=node.start_mark.line + 1,
                        column=node.start_mark.column + 1,
                    )
                ) from exc
        return value

    @staticmethod
    def _convert_key(node: Node) -> str:
        if not isinstance(node, ScalarNode):
            issue = ValidationIssue(
                code="ERR_YAML_COMPLEX_KEY",
                message="Mapping keys must be scalars",
                pointer="/",
                line=node.start_mark.line + 1,
                column=node.start_mark.column + 1,
            )
            raise YamlValidationError(issue)
        value = _YamlComposer._convert_scalar(node)
        if not isinstance(value, str):
            issue = ValidationIssue(
                code="ERR_YAML_COMPLEX_KEY",
                message="Mapping keys must be strings",
                pointer="/",
                line=node.start_mark.line + 1,
                column=node.start_mark.column + 1,
            )
            raise YamlValidationError(issue)
        return value


def _pointer_from_path(path: PointerPath) -> Pointer:
    if not path:
        return "/"
    return "/" + "/".join(str(part) for part in path)


def _lookup_location(pointer: Pointer, locations: Mapping[Pointer, Location]) -> Tuple[Optional[int], Optional[int]]:
    if pointer in locations:
        line, column = locations[pointer]
        return line, column
    if pointer == "/":
        return (None, None)
    parts = pointer.strip("/").split("/")
    while parts:
        candidate = "/" + "/".join(parts)
        if candidate in locations:
            line, column = locations[candidate]
            return line, column
        parts.pop()
    return (None, None)


class YamlLoaderV2:
    """Loads YAML v2 documents into Python dictionaries with strict validation."""

    DEFAULT_ALLOWED_ENGINES = {"lc.lcel"}

    def __init__(
        self,
        schema_path: Optional[Union[str, Path]] = None,
        *,
        allowed_runtime_engines: Optional[Iterable[str]] = None,
    ) -> None:
        root = Path(__file__).resolve().parents[2]
        self._schema_path = Path(schema_path) if schema_path else root / "schemas" / "yaml_v2.json"
        if not self._schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self._schema_path}")
        with self._schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        self._validator = Draft202012Validator(schema)
        engines = set(allowed_runtime_engines) if allowed_runtime_engines is not None else set(self.DEFAULT_ALLOWED_ENGINES)
        if not engines:
            raise ValueError("allowed_runtime_engines must not be empty")
        self._allowed_engines = engines

    def load_file(self, path: Union[str, Path]) -> Mapping[str, Any]:
        text = Path(path).read_text(encoding="utf-8")
        return self.loads(text, source=str(path))

    def loads(self, yaml_text: str, *, source: Optional[str] = None) -> Mapping[str, Any]:
        composer = _YamlComposer(yaml_text)
        document = composer.compose()
        locations = composer.locations
        if not isinstance(document, MutableMapping):
            issue = ValidationIssue(
                code="ERR_ROOT_NOT_MAPPING",
                message="Top-level YAML document must be a mapping",
                pointer="/",
                line=None,
                column=None,
                source=source,
            )
            raise YamlValidationError(issue)
        self._run_jsonschema(document, locations, source)
        self._validate_domains(document, locations, source)
        return document

    def _run_jsonschema(
        self,
        document: Mapping[str, Any],
        locations: Mapping[Pointer, Location],
        source: Optional[str],
    ) -> None:
        errors = sorted(self._validator.iter_errors(document), key=_jsonschema_error_sort_key)
        if not errors:
            return
        error = errors[0]
        pointer = _pointer_from_path(tuple(error.absolute_path))
        line, column = _lookup_location(pointer, locations)
        code = self._map_schema_error(error)
        issue = ValidationIssue(
            code=code,
            message=self._format_schema_error(error),
            pointer=pointer,
            line=line,
            column=column,
            source=source,
        )
        raise YamlValidationError(issue)

    def _validate_domains(
        self,
        document: Mapping[str, Any],
        locations: Mapping[Pointer, Location],
        source: Optional[str],
    ) -> None:
        self._assert_allowed_runtime_engine(document, locations, source)
        self._assert_unique_ids(document.get("providers", []), "providers", "ERR_PROVIDER_DUP", locations, source)
        self._assert_unique_ids(document.get("tools", []), "tools", "ERR_TOOL_DUP", locations, source)
        self._assert_unique_ids(document.get("components", []), "components", "ERR_COMPONENT_DUP", locations, source)
        graph = document.get("graph", {})
        if isinstance(graph, Mapping):
            self._assert_unique_ids(
                graph.get("nodes", []),
                "graph/nodes",
                "ERR_NODE_DUP",
                locations,
                source,
            )
            self._assert_unique_output_keys(graph.get("outputs", []), locations, source)

    def _assert_allowed_runtime_engine(
        self,
        document: Mapping[str, Any],
        locations: Mapping[Pointer, Location],
        source: Optional[str],
    ) -> None:
        runtime = document.get("runtime")
        if not isinstance(runtime, Mapping):
            return
        engine = runtime.get("engine")
        if engine is None:
            return
        if engine not in self._allowed_engines:
            pointer = "/runtime/engine"
            line, column = _lookup_location(pointer, locations)
            issue = ValidationIssue(
                code="ERR_RUNTIME_ENGINE_UNSUPPORTED",
                message=f"Runtime engine '{engine}' is not supported",
                pointer=pointer,
                line=line,
                column=column,
                source=source,
            )
            raise YamlValidationError(issue)

    def _assert_unique_ids(
        self,
        entries: Any,
        anchor: str,
        code: str,
        locations: Mapping[Pointer, Location],
        source: Optional[str],
    ) -> None:
        if not isinstance(entries, Sequence):
            return
        seen: Dict[str, int] = {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                continue
            identifier = entry.get("id")
            if not isinstance(identifier, str):
                continue
            if identifier in seen:
                pointer = f"/{anchor}/{index}/id"
                line, column = _lookup_location(pointer, locations)
                issue = ValidationIssue(
                    code=code,
                    message=f"Duplicate identifier '{identifier}' in {anchor}",
                    pointer=pointer,
                    line=line,
                    column=column,
                    source=source,
                )
                raise YamlValidationError(issue)
            seen[identifier] = index

    def _assert_unique_output_keys(
        self,
        entries: Any,
        locations: Mapping[Pointer, Location],
        source: Optional[str],
    ) -> None:
        if not isinstance(entries, Sequence):
            return
        seen: Dict[str, int] = {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, Mapping):
                continue
            key = entry.get("key")
            if not isinstance(key, str):
                continue
            if key in seen:
                pointer = f"/graph/outputs/{index}/key"
                line, column = _lookup_location(pointer, locations)
                issue = ValidationIssue(
                    code="ERR_OUTPUT_KEY_COLLISION",
                    message=f"Graph output key '{key}' is declared multiple times",
                    pointer=pointer,
                    line=line,
                    column=column,
                    source=source,
                )
                raise YamlValidationError(issue)
            seen[key] = index

    def _map_schema_error(self, error: JsonSchemaValidationError) -> str:
        schema_path = list(error.schema_path)
        if schema_path and schema_path[-1] == "const" and list(error.absolute_path) == ["meta", "version"]:
            return "ERR_META_VERSION_UNSUPPORTED"
        return "ERR_SCHEMA_VALIDATION"

    @staticmethod
    def _format_schema_error(error: JsonSchemaValidationError) -> str:
        return error.message


def _jsonschema_error_sort_key(error: JsonSchemaValidationError) -> Tuple[int, Tuple[Any, ...]]:
    path = tuple(error.absolute_path)
    return (len(path), path)


__all__ = ["YamlLoaderV2", "YamlValidationError", "ValidationIssue"]
