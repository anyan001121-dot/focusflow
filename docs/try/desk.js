"use strict";
const storageKey = "focusflow.browser.v1";
const $ = id => document.getElementById(id);
const state = { task: null, thoughts: [] };
try {
  const saved = JSON.parse(localStorage.getItem(storageKey));
  if (saved && Array.isArray(saved.thoughts)) Object.assign(state, saved);
} catch {
  $("notice").textContent = "无法读取保存的进度。";
}

function commit(message, updateView = render) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(state));
    $("notice").textContent = message;
  } catch {
    $("notice").textContent = "浏览器无法保存进度，关闭页面后可能丢失。";
  }
  updateView();
}

function render() {
  const task = state.task;
  $("draft").hidden = !!task;
  $("current").hidden = !task;
  if (task) {
    $("goal").textContent = task.title;
    $("state-heading").textContent = task.paused ? "暂停书签" : "眼前这一小步";
    $("step").value = task.step;
    $("step").readOnly = task.paused;
    $("step-form").querySelector("button").hidden = task.paused;
    $("note").value = task.note;
    $("pause-form").hidden = task.paused;
    $("return-note").textContent = task.note;
    $("return-note").hidden = !task.paused || !task.note;
    $("resume").hidden = !task.paused;
    $("done").hidden = task.paused;
  }
  renderShelf();
}

function renderShelf() {
  $("thoughts").replaceChildren(...state.thoughts.map((thought, index) => {
    const item = document.createElement("li");
    const label = document.createElement("span");
    label.textContent = thought;
    const clear = document.createElement("button");
    clear.type = "button";
    clear.className = "quiet";
    clear.textContent = "移除";
    clear.setAttribute("aria-label", "移除暂存事项：" + thought);
    clear.onclick = () => {
      state.thoughts.splice(index, 1);
      commit("已移除暂存事项。", renderShelf);
      $("thought").focus();
    };
    item.append(label, clear);
    return item;
  }));
}

function suggest(title) {
  if (/论文|报告|文档|写作/.test(title)) return "打开对应文档，先写一条想讲的要点。";
  if (/邮件|回复|回信/.test(title)) return "打开那封邮件，先写一句你想回复的重点。";
  if (/复习|学习|刷题/.test(title)) return "打开学习材料，挑一道题或一小段先看。";
  return "打开要用的材料，写下一个两分钟内能动手的动作。";
}

function submit(id, action) {
  $(id).addEventListener("submit", event => {
    event.preventDefault();
    action();
  });
}
let ai = null;
let starting = false;
const localRelay = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);
if (localRelay) $("ai-endpoint").value = new URL("/api/step", location.origin).href;

$("ai-settings-link").addEventListener("click", event => {
  event.preventDefault();
  $("ai-settings").open = true;
  $("ai-endpoint").focus();
});

submit("ai-form", () => {
  let endpoint;
  try {
    endpoint = new URL($("ai-endpoint").value.trim());
    const loopback = ["localhost", "127.0.0.1", "[::1]"].includes(endpoint.hostname);
    if ((endpoint.protocol !== "https:" && !(loopback && endpoint.protocol === "http:")) ||
        endpoint.username || endpoint.password || endpoint.hash || endpoint.search) {
      throw new Error("invalid endpoint");
    }
  } catch {
    $("ai-status").textContent = "请输入 HTTPS 接口地址。本机接口可以用 HTTP，地址里请勿附带令牌。";
    return;
  }
  ai = {
    endpoint: endpoint.href,
    token: $("ai-token").value.trim() || (ai?.endpoint === endpoint.href ? ai.token : ""),
    prompt: $("ai-prompt").value.trim(),
  };
  $("ai-token").value = "";
  $("ai-mode").textContent = "AI 模式";
  $("ai-off").hidden = false;
  $("ai-status").textContent = "已启用。点击「出发咯」时会连接 " + endpoint.host + "。";
});

$("ai-off").onclick = () => {
  ai = null;
  $("ai-token").value = "";
  $("ai-off").hidden = true;
  $("ai-mode").textContent = "离线模式";
  $("ai-status").textContent = "已切回离线模板。";
};

async function requestStep(title, config) {
  const headers = { "Content-Type": "application/json" };
  if (config.token) headers.Authorization = "Bearer " + config.token;
  const response = await fetch(config.endpoint, {
    method: "POST",
    headers,
    credentials: "omit",
    redirect: "error",
    signal: AbortSignal.timeout(15000),
    body: JSON.stringify({ task: title, prompt: config.prompt }),
  });
  if (response.status === 401 || response.status === 403) throw new Error("接口未授权，请检查访问令牌");
  if (response.status === 429) throw new Error("接口暂时限流，请稍后重试");
  if (!response.ok) throw new Error("接口暂不可用");
  const result = await response.json();
  const step = typeof result?.step === "string" ? result.step.trim() : "";
  if (!step || step.length > 500) throw new Error("接口没有返回可用的步骤");
  return step;
}

submit("start", async () => {
  const title = $("task").value.trim();
  if (!title || starting) return;
  const config = ai;
  let step = suggest(title);
  let message = "已找到一个起点。";
  if (config) {
    const button = $("start").querySelector("button");
    starting = true;
    button.disabled = true;
    $("task").readOnly = true;
    button.textContent = "正在找第一步…";
    $("notice").textContent = "正在连接 AI 接口。";
    try {
      step = await requestStep(title, config);
      message = "AI 找到了一个起点，你可以再改小一点。";
    } catch (error) {
      const reason = error.name === "TimeoutError" ? "连接超时" :
        error.name === "TypeError" || error.name === "SyntaxError" ? "接口连接或返回格式有误" : error.message;
      message = reason + "。这次先用离线建议。";
      $("ai-status").textContent = message;
    } finally {
      starting = false;
      button.disabled = false;
      $("task").readOnly = false;
      button.textContent = "出发咯";
    }
  }
  state.task = { title, step, note: "", paused: false };
  $("task").value = "";
  commit(message);
  $("step").focus();
});
submit("step-form", () => {
  if (!state.task || state.task.paused || !$("step").value.trim()) return;
  state.task.step = $("step").value.trim();
  commit("步骤已保存。");
});
submit("pause-form", () => {
  const step = $("step").value.trim();
  if (step) state.task.step = step;
  state.task.note = $("note").value.trim();
  state.task.paused = true;
  commit("书签已保存。");
  $("resume").focus();
});
$("resume").onclick = () => {
  state.task.paused = false;
  commit("从这里接着来。");
  $("step").focus();
};
$("done").onclick = () => {
  state.task = null;
  commit("这一步完成了。");
  $("task").focus();
};
submit("capture", () => {
  const thought = $("thought").value.trim();
  if (!thought) return;
  state.thoughts.push(thought);
  $("thought").value = "";
  commit("念头已暂存。", renderShelf);
});
render();
