"""Bounded agent loop: converse, optionally run one safe SQL tool, then answer."""

import json
from pathlib import Path

from .config import ProviderConfig
from .conversation import Conversation
from .guardrails import validate_question
from .prompts import coverage_evidence
from .provider import ProviderError, build_request, continue_request, request_turn
from .query import QueryError, execute_query
from .storage import read_report

MAX_TOOL_BYTES = 32_000


def tool_evidence(result: dict) -> str:
    """Send selected computed evidence only, never raw audit records or credentials."""
    evidence = {key: result[key] for key in ('sql', 'columns', 'rows', 'explanation')}
    evidence['coverage'] = coverage_evidence(result['coverage'])
    encoded = json.dumps(evidence, ensure_ascii=False, allow_nan=False)
    if len(encoded.encode('utf-8')) > MAX_TOOL_BYTES:
        raise ProviderError('Result exceeds the 32 KB sharing budget; narrow the query to summarize it')
    return encoded


def ask(question: str, database: Path, config: ProviderConfig, include_summary: bool = True,
        conversation: Conversation | None = None) -> dict:
    question = validate_question(question)
    coverage = read_report(database)
    payload = build_request(question, coverage, config, conversation.messages if conversation else None)
    first = request_turn(payload, config)
    result = {'question': question, 'coverage': coverage, 'model': config.model,
              'provider': config.provider, 'provider_calls': 1, 'provider_elapsed_ms': first['elapsed_ms']}
    call = first['tool_call']
    if call is None:
        result.update(status='conversation', answer=first['text'])
    else:
        arguments = call['arguments']
        result.update(sql=arguments['sql'], explanation=arguments['explanation'])
        try:
            result.update(execute_query(database, arguments['sql']))
            result['status'] = 'answered'
        except QueryError as exc:
            # Error stays an error even when the model explains it conversationally.
            result.update(status='query_error', tool_error=str(exc),
                          answer='I could not run that query safely. Try narrowing or rephrasing the question.')
        if include_summary:
            try:
                output = (json.dumps({'error': result['tool_error'], 'query_executed': False})
                          if result['status'] == 'query_error' else tool_evidence(result))
                followup = continue_request(payload, first, output, config, result['status'] == 'query_error')
                result['provider_calls'] = 2
                final = request_turn(followup, config, allow_tools=False)
                result.update(answer=final['text'], summary_elapsed_ms=final['elapsed_ms'])
            except (ValueError, OSError) as exc:
                # A prose failure never discards successful local evidence. No retries.
                result['summary_error'] = str(exc)
    if conversation is not None:
        conversation.remember(question, result)
    return result
