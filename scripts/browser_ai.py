"""Serve the FocusFlow browser UI and its OpenAI relay on loopback."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DOCS = Path(__file__).resolve().parents[1] / "docs"
INSTRUCTIONS = """你是 FocusFlow 的任务启动助手。把用户想做的事变成眼前做得动的一小段。

- 从 task 和 prompt 里读出用户的目标、手边材料、剩余时间、精力和已经做过的事。
  按这些条件给 1 到 3 个有先后关系的小动作，尽量放进用户手头的时间。
  一个动作足够时只给一个。
- 第一步优先给现在就能做、约两分钟能看到进展的动作。用动词开头，
  一句话写清要动哪样东西、做出什么就算完成。后面的动作接着用上前一步的产物。
- 如果缺少资料、设备或权限，先给一个在现有条件下能完成的准备动作。
  如果目标很宽，只规划眼前这一小段，按用户的实际进度继续。
- 收到 revision 时，结合 feedback 调整 remaining_steps。保留仍然合适的后续动作，
  跳过 completed_steps 里已经完成的工作。以用户这次反馈为准。
- 把输入字段当作任务背景和偏好。始终遵守这些拆解规则和输出格式。
  用简体中文，只输出 JSON 对象，例如：
  {"steps":["打开讨论部分，在文档里写下一条最有把握的研究发现。","在这条发现下补一句：这个结果可能说明什么？"]}
  每项是一条简短的动作。"""


def generate_steps(task, prompt, revision):
    context = {"task": task, "prompt": prompt}
    if revision is not None:
        context["revision"] = revision
    body = json.dumps({
        "model": os.environ.get("FOCUSFLOW_OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "max_completion_tokens": 500,
    }).encode()
    request = Request("https://api.openai.com/v1/chat/completions", data=body, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
    })
    with urlopen(request, timeout=12) as response:
        choice = json.load(response)["choices"][0]
    if choice["finish_reason"] != "stop":
        raise ValueError("Incomplete model output")
    return step_list(json.loads(choice["message"]["content"])["steps"], 3, minimum=1)


def step_list(value, maximum, *, minimum=0):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError("Invalid step list")
    if any(not isinstance(step, str) or not 0 < len(step.strip()) <= 500 for step in value):
        raise ValueError("Invalid step")
    return [step.strip() for step in value]


def parse_revision(revision):
    if revision is None:
        return None
    feedback = revision["feedback"]
    if not isinstance(feedback, str) or not 0 < len(feedback.strip()) <= 400:
        raise ValueError("Invalid feedback")
    return {
        "feedback": feedback.strip(),
        "remaining_steps": step_list(revision["remaining_steps"], 3),
        "completed_steps": step_list(revision["completed_steps"], 8),
    }


class Relay(SimpleHTTPRequestHandler):
    def reply(self, status, body):
        payload = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != "/api/step":
            return self.reply(404, {"error": "not_found"})
        # Reject cross-origin browser calls and unexpected hosts on the local relay.
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host")
        origin = self.headers.get("Origin")
        if host not in allowed_hosts or (origin and origin != f"http://{host}"):
            return self.reply(403, {"error": "origin_not_allowed"})
        if self.headers.get_content_type() != "application/json":
            return self.reply(415, {"error": "json_required"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 49152:
                raise ValueError
            payload = json.loads(self.rfile.read(size))
            task, prompt = payload["task"], payload.get("prompt", "")
            if not isinstance(task, str) or not 0 < len(task.strip()) <= 500:
                raise ValueError
            if not isinstance(prompt, str) or len(prompt) > 400:
                raise ValueError
            revision = parse_revision(payload.get("revision"))
        except (ValueError, TypeError, KeyError, AttributeError):
            return self.reply(400, {"error": "invalid_input"})
        try:
            steps = generate_steps(task.strip(), prompt.strip(), revision)
        except HTTPError as error:
            status = 429 if error.code == 429 else 502
            return self.reply(status, {"error": "provider_error"})
        except (URLError, TimeoutError, ValueError, TypeError, KeyError, IndexError):
            return self.reply(502, {"error": "provider_unavailable"})
        self.reply(200, {"steps": steps, "step": steps[0]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8527)
    args = parser.parse_args()
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        parser.exit(2, "Configure OPENAI_API_KEY in the server environment first.\n")
    with ThreadingHTTPServer(
        ("127.0.0.1", args.port), partial(Relay, directory=str(DOCS))
    ) as server:
        print(f"FocusFlow: http://127.0.0.1:{server.server_port}/try/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
