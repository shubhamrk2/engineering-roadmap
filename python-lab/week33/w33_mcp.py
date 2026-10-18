"""Week 33: the pure-Python half of an MCP server.

No SDK, no network, no model. You build the pieces that every MCP server contains underneath the
framework: a JSON-RPC 2.0 message layer, an argument validator, a tool registry with an approval gate,
an output screen for prompt injection, and a tiny dispatcher for tools/list and tools/call.

Replace each stub with your own code.   Run:  pytest week33
"""
import json
import re

# ---------------------------------------------------------------------------------------------------
# Given to you
# ---------------------------------------------------------------------------------------------------
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

SUPPORTED_VERSIONS = ("2025-11-25", "2025-06-18")
TOOL_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class JsonRpcError(Exception):
    """Raised for a malformed message. Carries the JSON-RPC error code to send back."""

    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class UnknownTool(KeyError):
    """Raised by ToolRegistry.call when the tool does not exist (or is not on the allow-list)."""


# ---------------------------------------------------------------------------------------------------
# Part 1: JSON-RPC 2.0 messages
# ---------------------------------------------------------------------------------------------------
def make_request(id, method, params=None):
    """Build a request dict: {"jsonrpc": "2.0", "id": id, "method": method} plus "params" ONLY when
    params is not None.

    id must be a str or an int. None, a float and a bool (True is an int in Python!) are not allowed:
    raise ValueError. method must be a non-empty str, else ValueError.
    """
    raise NotImplementedError("Replace this stub with your own code")


def make_notification(method, params=None):
    """Build a notification: like a request but it has NO "id" key at all (not even None).
    Same method rule as make_request; "params" only when not None."""
    raise NotImplementedError("Replace this stub with your own code")


def make_result(id, result):
    """Build a success response: {"jsonrpc": "2.0", "id": id, "result": result}.
    result must be a dict (MCP results are objects), else ValueError. id rules as make_request."""
    raise NotImplementedError("Replace this stub with your own code")


def make_error(id, code, message, data=None):
    """Build an error response: {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}
    plus "data" inside "error" only when data is not None.

    Unlike a request, id MAY be None here (the server could not read the id of a broken request).
    code must be an int (not bool); message a str: else ValueError. id, when not None, is a str or int.
    """
    raise NotImplementedError("Replace this stub with your own code")


def classify_message(msg):
    """Validate one decoded message and return "request", "notification", "result" or "error".

    Raise JsonRpcError(INVALID_REQUEST, ...) when:
      - msg is not a dict (a JSON array is a batch; MCP does not allow batches)
      - "jsonrpc" is not exactly the string "2.0"
      - it has "method": the method must be a str; if "id" is present it must be a str or an int
        (not None, not bool, not float) -> request; if "id" is absent -> notification
      - it has no "method": it must have an "id" and exactly ONE of "result" / "error"
          * "result" must be a dict -> "result"; id must be str or int
          * "error" must be a dict with an int "code" (not bool) and a str "message" -> "error".
            For an error response id may be None.
      - anything else
    """
    raise NotImplementedError("Replace this stub with your own code")


def parse_message(raw):
    """Decode one line of JSON text and validate it. Return (kind, message_dict).

    Invalid JSON -> JsonRpcError(PARSE_ERROR, ...). Everything else is classify_message's job.
    """
    raise NotImplementedError("Replace this stub with your own code")


class RequestTracker:
    """Client-side bookkeeping of requests that have been sent and not answered yet.

    next_id()      -> 1, 2, 3 ... (an int, increasing by one on every call, starting at 1)
    track(id)      -> remember that id is outstanding. ValueError if it is already outstanding
                      (the spec: an id MUST NOT match one still waiting for a response).
    complete(msg)  -> msg is a response (kind "result" or "error"). Remove its id from the
                      outstanding set and return the id. If that id is not outstanding (or the
                      id is None) raise KeyError. A request/notification raises ValueError.
    pending        -> property: sorted list of outstanding ids (ints before strs is not needed:
                      all test ids are the same type).
    """

    def __init__(self):
        raise NotImplementedError("Replace this stub with your own code")

    def next_id(self):
        raise NotImplementedError("Replace this stub with your own code")

    def track(self, id):
        raise NotImplementedError("Replace this stub with your own code")

    def complete(self, msg):
        raise NotImplementedError("Replace this stub with your own code")

    @property
    def pending(self):
        raise NotImplementedError("Replace this stub with your own code")


# ---------------------------------------------------------------------------------------------------
# Part 2: validating tool arguments against a JSON Schema subset
# ---------------------------------------------------------------------------------------------------


def validate_arguments(schema, arguments):
    """Check `arguments` against `schema` and return a list of error strings ([] means valid).

    Never raise for bad input; report it. Supported keywords:
      type: object / string / integer / number / boolean / array / null
            (a bool is NOT an integer or a number; an int IS a number)
      object:  properties, required, additionalProperties (only the value False matters)
      string:  enum, minLength, maxLength, pattern (use re.search)
      number / integer: minimum, maximum (inclusive), enum
      array:   items (a schema applied to every element)

    Each error string STARTS WITH the path of the offending value, then ": ", then a reason:
      top-level property:  "ticket_id: expected string"
      missing required:    "ticket_id: required"
      extra property:      "colour: unexpected property"
      array element:       "tags[1]: expected string"
      nested property:     "address.zip: required"
      arguments not a dict: "arguments: expected object"
    Report every problem, not just the first. If a value has the wrong type, report only the type
    error for that value (do not also check its other keywords).
    """
    raise NotImplementedError("Replace this stub with your own code")


# ---------------------------------------------------------------------------------------------------
# Part 3: a tool registry with read/write classification and an approval gate
# ---------------------------------------------------------------------------------------------------
class ToolRegistry:
    """Holds tools and runs them safely.

    ToolRegistry(allow=None): `allow` is None (everything registered is visible) or a set of tool
    names. A tool NOT in a non-None allow-set is invisible: list_tools omits it and call raises
    UnknownTool, exactly as if it did not exist.

    register(name, handler, schema, description, access="read")
        name must match TOOL_NAME_RE, access must be "read" or "write", and the name must not be
        registered already: otherwise raise ValueError.

    list_tools() -> list of dicts, sorted by name (deterministic order), each:
        {"name", "description", "inputSchema": schema, "annotations": {"readOnlyHint": access == "read"}}

    call(name, arguments, approver=None) -> an MCP CallToolResult dict:
        {"content": [{"type": "text", "text": ...}], "isError": bool}  (+ "structuredContent" for dicts)
      Order of checks:
        1. unknown / not allowed tool -> raise UnknownTool(name)
        2. arguments invalid per validate_arguments -> isError True, text "Invalid arguments: " + "; ".join(errors),
           handler NOT called, approver NOT called
        3. access == "write": approver is None -> isError True, text "Approval required for 'NAME'".
           approver(name, arguments) returns False -> isError True, text "Denied: 'NAME'". True -> go on.
           (read tools never call the approver)
        4. run handler(**arguments). If it raises, return isError True with text "Tool 'NAME' failed"
           and NOTHING from the exception (no message, no class name): internals must not leak.
        5. success: a str result becomes the text unchanged. Anything else becomes
           json.dumps(result, sort_keys=True) as the text, and a dict result is also returned as
           "structuredContent". isError False.
    """

    def __init__(self, allow=None):
        raise NotImplementedError("Replace this stub with your own code")

    def register(self, name, handler, schema, description, access="read"):
        raise NotImplementedError("Replace this stub with your own code")


    def list_tools(self):
        raise NotImplementedError("Replace this stub with your own code")

    def call(self, name, arguments, approver=None):
        raise NotImplementedError("Replace this stub with your own code")


# ---------------------------------------------------------------------------------------------------
# Part 4: screening tool output for instruction-like text
# ---------------------------------------------------------------------------------------------------
INJECTION_RULES = {
    "ignore_previous": re.compile(r"ignore\s+(all\s+|any\s+)?(previous|prior|above|earlier)\s+(instructions|rules|messages)", re.I),
    "role_override": re.compile(r"\b(you are now|act as|new system prompt|system prompt:)", re.I),
    "exfiltrate": re.compile(r"\b(send|post|forward|upload|email)\b[^.\n]{0,80}\b(https?://|to\s+\S+@\S+)", re.I),
    "tool_directive": re.compile(r"\b(call|invoke|run|use)\s+the\s+[\w.-]+\s+tool\b", re.I),
    "hidden_markup": re.compile(r"<\s*/?\s*(important|system|instructions?)\s*>", re.I),
    "secret_request": re.compile(r"\b(reveal|print|show|send|include)\b[^.\n]{0,40}\b(api[ _-]?key|password|token|secret|credentials?)\b", re.I),
}
ZERO_WIDTH = "".join(map(chr, (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF)))   # zero-width space, non-joiner, joiner, word joiner, BOM
OPEN_TAG = '<tool_output untrusted="true">'
CLOSE_TAG = "</tool_output>"


def flag_injection(text):
    """Return the sorted list of INJECTION_RULES names whose pattern matches `text`.

    Zero-width characters (ZERO_WIDTH) are removed from the text BEFORE matching, because attackers
    hide words with them (a zero-width space hidden inside the word "ignore"). Additionally, if the text
    contained any zero-width character, add the rule name "zero_width" to the result.
    A clean string returns []. Non-str input returns [].
    """
    raise NotImplementedError("Replace this stub with your own code")


def screen_result(result):
    """Prepare a CallToolResult for a model that must treat it as DATA, not instructions.

    Return {"flags": sorted unique list of rule names over ALL text items, "result": copy}.
    The copy has every {"type": "text"} item rewritten as
        OPEN_TAG + cleaned_text + CLOSE_TAG
    where cleaned_text has zero-width characters removed and any literal CLOSE_TAG inside it
    replaced by "&lt;/tool_output&gt;" (so the data cannot close the wrapper early and escape).
    Non-text items are copied unchanged. Other keys (isError, structuredContent) are kept.
    The input dict must NOT be modified.
    """
    raise NotImplementedError("Replace this stub with your own code")


# ---------------------------------------------------------------------------------------------------
# Part 5: a tiny in-memory server
# ---------------------------------------------------------------------------------------------------
def handle_message(registry, msg, approver=None):
    """Handle ONE decoded message and return the response dict, or None when no response is allowed.

    Use classify_message first. A message that fails validation -> make_error(None, INVALID_REQUEST, ...)
    (the id could not be trusted, so it is None).

    A notification NEVER gets a response (return None), even for an unknown method.

    Requests, by method:
      "initialize"  params.protocolVersion: if it is in SUPPORTED_VERSIONS echo it back, else answer
                    with SUPPORTED_VERSIONS[0]. result = {"protocolVersion": that, "capabilities":
                    {"tools": {}}, "serverInfo": {"name": "w33-server", "version": "0.1"}}
      "ping"        result {}
      "tools/list"  result {"tools": registry.list_tools()}
      "tools/call"  params must be a dict whose "name" is a str and whose "arguments" (default {}) is a
                    dict: otherwise make_error(id, INVALID_PARAMS, ...). An unknown tool is a PROTOCOL
                    error: make_error(id, INVALID_PARAMS, "Unknown tool: NAME"). Otherwise the result is
                    registry.call(name, arguments, approver) (tool failures are isError results, NOT
                    JSON-RPC errors).
      anything else make_error(id, METHOD_NOT_FOUND, "Method not found: METHOD")
    The response id always equals the request id.
    """
    raise NotImplementedError("Replace this stub with your own code")


def handle_line(registry, line, approver=None):
    """Handle one raw line of text (what arrives on stdin). Return the response as a JSON string
    (json.dumps, no embedded newline) or None when there is nothing to send.

    Invalid JSON -> a PARSE_ERROR response with id None. Otherwise delegate to handle_message.
    """
    raise NotImplementedError("Replace this stub with your own code")
