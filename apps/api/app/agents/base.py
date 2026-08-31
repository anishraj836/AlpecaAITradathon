import time
import json
import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone
from app.domain.models import AgentTraceStep, AgentRole, Tag, AgentTraceDetails

TInput = TypeVar('TInput', bound=BaseModel)
TOutput = TypeVar('TOutput', bound=BaseModel)

logger = logging.getLogger("VoltronAgent")

class BaseAgent(ABC, Generic[TInput, TOutput]):
    """
    Common runtime abstraction for VOLTRON AI reasoning agents.
    Provides structured prompt formatting, timing, latency tracking,
    trace step creation, and robust JSON schema parsing.
    """

    def __init__(
        self,
        role: AgentRole,
        label: str,
        output_cls: Type[TOutput],
        system_prompt_path: Optional[str] = None,
    ):
        self.role = role
        self.label = label
        self.output_cls = output_cls
        self.system_prompt = self._load_prompt(system_prompt_path) if system_prompt_path else ""
        self.last_execution_mode: str = "LLM_REASONING"
        self.last_provider_name: Optional[str] = None
        self.last_model_name: Optional[str] = None

    def _load_prompt(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not load prompt from {path}: {e}")
            return ""

    @abstractmethod
    async def _execute_reasoning(self, input_data: TInput) -> TOutput:
        """Subclasses implement specific LLM reasoning logic or structured deterministic fallback."""
        pass

    async def run(
        self,
        input_data: TInput,
        decision_id: str,
        step_id: str,
        title: str,
    ) -> tuple[TOutput, AgentTraceStep]:
        start_time = time.perf_counter()
        timestamp_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

        try:
            output = await self._execute_reasoning(input_data)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Build AgentTraceStep
            trace_step = self._create_trace_step(
                step_id=step_id,
                title=title,
                status="COMPLETE",
                elapsed_ms=elapsed_ms,
                output=output,
            )
            return output, trace_step

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Agent [{self.label}] execution failed: {e}", exc_info=True)
            
            trace_step = AgentTraceStep(
                id=step_id,
                agentRole=self.role,
                agentLabel=self.label,
                title=title,
                timestampOffset=f"T+{elapsed_ms}ms",
                status="FAILED",
                summary=f"Agent execution encountered an error: {str(e)}",
                confidenceScore=0.0,
                tags=[Tag(label="FAILED", variant="error")],
                executionMode="HEURISTIC_FALLBACK",
            )
            raise e

    def _create_trace_step(
        self,
        step_id: str,
        title: str,
        status: str,
        elapsed_ms: int,
        output: TOutput,
    ) -> AgentTraceStep:
        summary_val = getattr(output, "summary", str(output))
        confidence_val = getattr(output, "confidence", 0.8)

        tags = [
            Tag(label=f"T+{elapsed_ms}ms", variant="secondary"),
            Tag(label=f"{int(confidence_val * 100)}% Conf", variant="tertiary" if confidence_val >= 0.75 else "warning"),
        ]

        if self.last_execution_mode == "LLM_REASONING" and self.last_provider_name:
            tags.append(Tag(label=f"LLM: {self.last_provider_name.upper()}", variant="primary"))
        elif self.last_execution_mode == "HEURISTIC_FALLBACK":
            tags.append(Tag(label="FALLBACK HEURISTIC", variant="error"))

        return AgentTraceStep(
            id=step_id,
            agentRole=self.role,
            agentLabel=self.label,
            title=title,
            timestampOffset=f"T+{elapsed_ms}ms",
            status="COMPLETE",
            summary=summary_val,
            confidenceScore=confidence_val,
            tags=tags,
            executionMode=self.last_execution_mode,
            providerName=self.last_provider_name,
            modelName=self.last_model_name,
        )
