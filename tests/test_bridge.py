import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from foundation_template.tools import BOUNDARY, TOOL_NAMES, input_sha256
from foundation_template_bridge.schemas import tool_definitions
from foundation_template_bridge.server import LIMITS, PROTOCOL, Bridge, encode_response, serve

ROOT = Path(__file__).resolve().parents[1]
INIT = {"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": {"protocolVersion": PROTOCOL}}


def session(*frames, argv=()):
    raw = b"".join((f if type(f) is bytes else json.dumps(f).encode()) + b"\n" for f in frames)
    proc = subprocess.run([sys.executable, "-B", "-m", "foundation_template_bridge", *argv], cwd=ROOT, input=raw,
                          capture_output=True, timeout=30)
    return proc, [json.loads(line) for line in proc.stdout.splitlines()]


def call(arguments, name="echo_observation", ident=1):
    return {"jsonrpc": "2.0", "id": ident, "method": "tools/call", "params": {"name": name, "arguments": arguments}}


class BridgeTests(unittest.TestCase):
    def test_handshake_catalog_and_echo_with_evidence(self):
        proc, (hello, catalog, echoed) = session(INIT, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                                                 call({"observation": "reading 7"}))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual((hello["result"]["protocolVersion"], hello["result"]["mcpCompatible"]), (PROTOCOL, False))
        self.assertEqual(catalog["result"]["tools"], tool_definitions())
        self.assertEqual(tuple(t["name"] for t in catalog["result"]["tools"]), TOOL_NAMES)
        result = echoed["result"]
        receipt = result["structuredContent"]["receipt"]
        self.assertFalse(result["isError"])
        self.assertEqual(result["structuredContent"]["assessment"], "observation_echoed")
        self.assertEqual((receipt["result"], receipt["boundary"], receipt["status"]),
                         ({"observation": "reading 7"}, BOUNDARY, "ok"))
        self.assertEqual(receipt["input_sha256"], input_sha256({"observation": "reading 7"}))
        self.assertEqual(receipt["evidence"][0]["evidence"]["status"], "CHECK")

    def test_bad_arguments_are_a_tool_error_that_still_carries_evidence(self):
        for arguments in ({}, {"observation": ""}, {"observation": 3}, {"observation": "x", "extra": 1},
                          {"observation": "x" * 257}):
            _, (_, reply) = session(INIT, call(arguments))
            result = reply["result"]
            self.assertTrue(result["isError"], arguments)
            self.assertEqual(result["structuredContent"]["receipt"]["status"], "error")
            self.assertTrue(result["structuredContent"]["receipt"]["evidence"])

    def test_wire_profile_fails_closed(self):
        for frame, code in ((b'{"jsonrpc":"2.0","id":1,"id":2,"method":"ping"}', -32700),
                            (b'{"jsonrpc":"2.0","id":1,"method":"ping","x":1.5}', -32700),
                            (b'{"jsonrpc":"2.0","id":1,"method":"ping","x":NaN}', -32700),
                            (b"[" * 33 + b"]" * 33, -32002)):
            _, (_, reply) = session(INIT, frame)
            self.assertEqual(reply["error"]["code"], code, frame)
        _, (reply,) = session(call({"observation": "x"}))
        self.assertEqual(reply["error"]["code"], -32000)
        _, (_, reply) = session(INIT, call({}, name="read_file"))
        self.assertEqual(reply["error"]["code"], -32602)
        proc, _ = session(INIT, argv=("--root", "/"))
        self.assertEqual(proc.returncode, 2)

    def test_source_manifest_lists_every_file(self):
        manifest = json.loads((ROOT / "SOURCE-MANIFEST.json").read_text())["files"]
        actual = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(ROOT.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and ".git" not in p.parts
                  and p.relative_to(ROOT).parts[0] != ".github" and p.suffix != ".pyc" and p.name != "SOURCE-MANIFEST.json"}
        self.assertEqual(manifest, actual, "run: python -B tools/build_manifest.py, then re-pin the adapter")


PING = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
LIST = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}


class FailingSink:
    def write(self, data):
        raise BrokenPipeError(32, "Broken pipe")

    def flush(self):
        raise BrokenPipeError(32, "Broken pipe")


class GapTests(unittest.TestCase):
    def test_gap_tpl_001_handshake_order_and_protocol_version(self):
        wrong = {"jsonrpc": "2.0", "id": "old", "method": "initialize", "params": {"protocolVersion": "mcp/2025"}}
        again = dict(INIT, id="again")
        proc, replies = session(wrong, LIST, INIT, again, dict(LIST, id=3))
        self.assertEqual(proc.returncode, 0)
        self.assertEqual([reply["id"] for reply in replies], ["old", 2, "init", "again", 3])
        self.assertEqual(replies[0]["error"]["code"], -32001)
        self.assertIn(PROTOCOL, replies[0]["error"]["message"])
        self.assertEqual(replies[1]["error"]["code"], -32000)
        self.assertEqual(replies[2]["result"]["protocolVersion"], PROTOCOL)
        self.assertEqual(replies[3]["error"], {"code": -32000, "message": "Bridge already initialized"})
        self.assertEqual(replies[4]["result"]["tools"], tool_definitions())
        _, (reply,) = session(LIST)
        self.assertEqual(reply, {"jsonrpc": "2.0", "id": 2, "error": {
            "code": -32000, "message": "Initialize the bridge before using tools"}})

    def test_gap_tpl_002_oversized_or_unencodable_response_is_withheld(self):
        limit = LIMITS["outputFrameBytes"]
        base = len(encode_response({"jsonrpc": "2.0", "id": 1, "result": {"x": ""}})) - 1
        fits = {"jsonrpc": "2.0", "id": 1, "result": {"x": "a" * (limit - base)}}
        raw = encode_response(fits)
        self.assertEqual(len(raw), limit + 1)
        self.assertEqual(json.loads(raw), fits)
        over = {"jsonrpc": "2.0", "id": 1, "result": {"x": "a" * (limit - base + 1)}}
        self.assertEqual(json.loads(encode_response(over)), {"jsonrpc": "2.0", "id": 1, "error": {
            "code": -32002, "message": "Result withheld"}})
        circular = {}
        circular["self"] = circular
        for result in ({"x": float("nan")}, {"x": float("inf")}, circular, {"x": {1, 2}}, {"x": object()}):
            with self.subTest(result=type(result.get("x", result)).__name__):
                raw = encode_response({"jsonrpc": "2.0", "id": "r", "result": result})
                self.assertTrue(raw.endswith(b"\n"))
                self.assertEqual(json.loads(raw), {"jsonrpc": "2.0", "id": "r", "error": {
                    "code": -32603, "message": "Result withheld"}})

    def test_gap_tpl_003_unexpected_exception_becomes_internal_error(self):
        expected = {"code": -32603, "message": "Internal bridge error; no evidence result is available"}
        with mock.patch("foundation_template_bridge.server.run", side_effect=RuntimeError("secret detail")):
            bridge = Bridge()
            self.assertIn("result", bridge.dispatch(INIT))
            self.assertEqual(bridge.dispatch(call({"observation": "x"}, ident=7)),
                             {"jsonrpc": "2.0", "id": 7, "error": expected})
        with mock.patch("foundation_template_bridge.server.tool_definitions", side_effect=KeyError("k")):
            bridge = Bridge()
            bridge.dispatch(INIT)
            self.assertEqual(bridge.dispatch(LIST), {"jsonrpc": "2.0", "id": 2, "error": expected})
        self.assertEqual(Bridge().dispatch(PING), {"jsonrpc": "2.0", "id": 1, "result": {}})

    def test_gap_tpl_004_envelope_is_refused_and_notifications_get_no_reply(self):
        refused = ([PING], [], 1, "ping", None, dict(PING, extra=1), dict(PING, jsonrpc="1.0"),
                   {"id": 1, "method": "ping"}, dict(PING, method=1), dict(PING, method=""),
                   dict(PING, id=None), dict(PING, id=True), dict(PING, id=[1]), dict(PING, id={"a": 1}),
                   dict(PING, id="x" * (LIMITS["idCharacters"] + 1)))
        for message in refused:
            with self.subTest(message=message):
                reply = Bridge().handle(json.dumps(message).encode())
                self.assertEqual(reply["id"], None)
                self.assertEqual(reply["error"]["code"], -32600)
        longest = "x" * LIMITS["idCharacters"]
        self.assertEqual(Bridge().handle(json.dumps(dict(PING, id=longest)).encode()),
                         {"jsonrpc": "2.0", "id": longest, "result": {}})
        notification = {"jsonrpc": "2.0", "method": "ping"}
        silent_init = {"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": PROTOCOL}}
        proc, replies = session(notification, silent_init, dict(PING, id=3), LIST)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(replies, [{"jsonrpc": "2.0", "id": 3, "result": {}}, {"jsonrpc": "2.0", "id": 2, "error": {
            "code": -32000, "message": "Initialize the bridge before using tools"}}])

    def test_gap_tpl_005_unterminated_frame_and_broken_pipe_exit_2(self):
        sink = io.BytesIO()
        status = serve(io.BytesIO(json.dumps(PING).encode() + b"\n" + json.dumps(PING).encode()), sink)
        self.assertEqual(status, 2)
        first, last = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual(first, {"jsonrpc": "2.0", "id": 1, "result": {}})
        self.assertEqual((last["id"], last["error"]["code"]), (None, -32002))
        self.assertEqual(serve(io.BytesIO(json.dumps(PING).encode() + b"\n"), FailingSink()), 2)
        proc = subprocess.run([sys.executable, "-B", "-m", "foundation_template_bridge"], cwd=ROOT,
                              input=json.dumps(PING).encode(), capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)["error"]["code"], -32002)
        read_end, write_end = os.pipe()
        os.close(read_end)
        try:
            proc = subprocess.run([sys.executable, "-B", "-m", "foundation_template_bridge"], cwd=ROOT,
                                  input=json.dumps(PING).encode() + b"\n", stdout=write_end,
                                  stderr=subprocess.PIPE, timeout=30)
        finally:
            os.close(write_end)
        self.assertEqual((proc.returncode, proc.stderr), (2, b""))


if __name__ == "__main__":
    unittest.main()
