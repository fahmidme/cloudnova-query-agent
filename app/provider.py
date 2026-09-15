"""Native tool-call adapters; provider-specific wire formats stop at this boundary."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import ProviderConfig
from .prompts import system_prompt
from .query import MAX_QUESTION_CHARS, MAX_SQL_CHARS

ENDPOINT = 'https://api.openai.com/v1/responses'
MAX_REPLY_CHARS = 4000
TOOL_NAME = 'query_database'
TOOL_DESCRIPTION = (
    'Execute one read-only SQLite SELECT or non-recursive WITH query over the allowed '
    'invoices/accounts schema. Returns computed columns, rows and data-quality coverage. '
    'Use for business figures and record lookups; explain capabilities/definitions or '
    'ask clarifications directly. Limit details to 100 rows, label money units, follow '
    'the metric rules, and include relevant identifiers. Only one attempt per turn.'
)
TOOL_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'sql': {'type': 'string', 'description': 'One read-only SQLite query.'},
        'explanation': {'type': 'string', 'description': 'Brief metric interpretation, units and assumptions.'},
    },
    'required': ['sql', 'explanation'],
}


class ProviderError(ValueError):
    """Sanitized provider failure; never include raw responses or credentials."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError('Provider redirected the request; no credentials were forwarded')


def validate_call(name, call_id, arguments) -> dict:
    if name != TOOL_NAME or not isinstance(call_id, str) or not 1 <= len(call_id) <= 200:
        raise ProviderError('The model requested an unknown tool or an invalid call identifier')
    if not isinstance(arguments, dict) or set(arguments) != {'sql', 'explanation'}:
        raise ProviderError('The model returned invalid query arguments')
    for key, limit in [('sql', MAX_SQL_CHARS), ('explanation', 2000)]:
        value = arguments[key]
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ProviderError('The model returned empty or oversized query arguments')
    return {'id': call_id, 'name': name, 'arguments': arguments}


def checked_turn(texts: list, calls: list, continuation: list, allow_tools: bool) -> dict:
    if len(calls) > 1 or (calls and not allow_tools):
        raise ProviderError('The model exceeded the one-query tool budget')
    if any(not isinstance(text, str) for text in texts):
        raise ProviderError('The model returned invalid answer text')
    text = '\n'.join(texts).strip()
    if len(text) > MAX_REPLY_CHARS or (not calls and not text):
        raise ProviderError('The model returned an empty or oversized answer')
    return {'text': text, 'tool_call': calls[0] if calls else None, 'continuation': continuation}


def parse_response(response: dict, allow_tools: bool = True) -> dict:
    if not isinstance(response, dict) or response.get('status') != 'completed':
        raise ProviderError('OpenAI returned an incomplete or failed response')
    output = response.get('output')
    if not isinstance(output, list) or any(not isinstance(item, dict) for item in output):
        raise ProviderError('OpenAI returned an invalid response structure')
    texts, calls = [], []
    for item in output:
        kind = item.get('type')
        if kind == 'function_call':
            try:
                arguments = json.loads(item.get('arguments', ''))
            except (ValueError, TypeError):
                raise ProviderError('OpenAI returned unreadable tool arguments') from None
            calls.append(validate_call(item.get('name'), item.get('call_id'), arguments))
        elif kind == 'message':
            content = item.get('content')
            if not isinstance(content, list):
                raise ProviderError('OpenAI returned invalid message content')
            for block in content:
                if not isinstance(block, dict) or block.get('type') != 'output_text':
                    raise ProviderError('OpenAI refused or returned unsupported answer content')
                texts.append(block.get('text'))
        elif kind != 'reasoning':
            raise ProviderError('OpenAI returned an unsupported response item')
    # Preserve reasoning/function-call items for stateless Responses continuation.
    return checked_turn(texts, calls, output, allow_tools)


def parse_anthropic_response(response: dict, allow_tools: bool = True) -> dict:
    if not isinstance(response, dict) or response.get('stop_reason') not in {'end_turn', 'tool_use'}:
        raise ProviderError('Claude returned an incomplete or refused response')
    content = response.get('content')
    if not isinstance(content, list) or any(not isinstance(item, dict) for item in content):
        raise ProviderError('Claude returned invalid message content')
    texts, calls = [], []
    for item in content:
        kind = item.get('type')
        if kind == 'tool_use':
            calls.append(validate_call(item.get('name'), item.get('id'), item.get('input')))
        elif kind == 'text':
            texts.append(item.get('text'))
        elif kind not in {'thinking', 'redacted_thinking'}:
            raise ProviderError('Claude returned unsupported answer content')
    if bool(calls) != (response['stop_reason'] == 'tool_use'):
        raise ProviderError('Claude returned an inconsistent tool response')
    return checked_turn(texts, calls, [{'role': 'assistant', 'content': content}], allow_tools)


def build_request(question: str, coverage: dict, config: ProviderConfig,
                  history: list | None = None) -> dict:
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= MAX_QUESTION_CHARS:
        raise ProviderError(f'question must contain 1..{MAX_QUESTION_CHARS} characters')
    messages = list(history or []) + [{'role': 'user', 'content': question}]
    instructions = system_prompt(coverage)
    if config.provider == 'anthropic':
        return {'model': config.model, 'max_tokens': 2000, 'system': instructions,
                'messages': messages,
                'tools': [{'name': TOOL_NAME, 'description': TOOL_DESCRIPTION, 'input_schema': TOOL_SCHEMA}],
                'tool_choice': {'type': 'auto', 'disable_parallel_tool_use': True}}
    return {'model': config.model, 'store': False, 'max_output_tokens': 2000,
            'input': [{'role': 'system', 'content': instructions}] + messages,
            'tools': [{'type': 'function', 'name': TOOL_NAME, 'description': TOOL_DESCRIPTION,
                       'parameters': TOOL_SCHEMA, 'strict': True}],
            'tool_choice': 'auto', 'parallel_tool_calls': False,
            'include': ['reasoning.encrypted_content']}


def continue_request(payload: dict, turn: dict, tool_output: str, config: ProviderConfig,
                     is_error: bool = False) -> dict:
    """Pair the result with the exact call, then disable tools for the final answer."""
    call_id = turn['tool_call']['id']
    if config.provider == 'anthropic':
        result = {'type': 'tool_result', 'tool_use_id': call_id,
                  'content': tool_output, 'is_error': is_error}
        return {**payload, 'tool_choice': {'type': 'none'},
                'messages': payload['messages'] + turn['continuation'] +
                            [{'role': 'user', 'content': [result]}]}
    result = {'type': 'function_call_output', 'call_id': call_id, 'output': tool_output}
    return {**payload, 'tool_choice': 'none',
            'input': payload['input'] + turn['continuation'] + [result]}


def request_turn(payload: dict, config: ProviderConfig, allow_tools: bool = True) -> dict:
    parser = parse_anthropic_response if config.provider == 'anthropic' else parse_response
    turn, elapsed = request_payload(payload, config, lambda response: parser(response, allow_tools))
    return {**turn, 'elapsed_ms': elapsed}


def request_payload(payload: dict, config: ProviderConfig, parse) -> tuple[dict, float]:
    """Shared transport for bounded agent turns, with no retries."""
    if config.provider == "anthropic":
        endpoint = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": config.api_key, "anthropic-version": "2023-06-01"}
    else:
        endpoint = ENDPOINT
        if config.model == "gpt-5.6-luna":
            payload["reasoning"] = {"effort": "none"}
        headers = {"Authorization": f"Bearer {config.api_key}"}
    request = Request(endpoint, data=json.dumps(payload).encode(),
                      headers={**headers, "Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    try:
        with build_opener(NoRedirect()).open(request, timeout=config.timeout_seconds) as response:
            data = response.read(1_000_001)
            if len(data) > 1_000_000:
                raise ProviderError("Provider response exceeded the size limit")
            result = parse(json.loads(data))
    except HTTPError as exc:
        code = exc.code
        exc.close()
        raise ProviderError(f"{config.provider} HTTP {code}; check key/model access or rate limits. No automatic retry.") from None
    except (URLError, TimeoutError, OSError):
        raise ProviderError("Provider connection failed or timed out. Completion/usage may be uncertain; no automatic retry.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ProviderError("Provider returned an unreadable response") from None
    return result, round((time.monotonic() - started) * 1000, 2)
