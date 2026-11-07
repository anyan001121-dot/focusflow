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
submit("start", () => {
  const title = $("task").value.trim();
  if (!title) return;
  state.task = { title, step: suggest(title), note: "", paused: false };
  $("task").value = "";
  commit("已找到一个起点。");
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
