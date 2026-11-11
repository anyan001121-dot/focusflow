"use strict";
const storageKey = "focusflow.browser.v2";
const legacyKey = "focusflow.browser.v1";
const $ = id => document.getElementById(id);
let state = { activeId: null, tasks: [], thoughts: [], returnTrail: [] };
let stored = null;
let starting = false;
let treeOpen = false;
let treeActiveId = null;
const expandedTasks = new Set();
const childDrafts = new Map();
let reviewOpen = false;
let reviewId = null;
let summarizedIds = [];
const summarySelection = new Set();
let recapId = null;
let distractionTaskId = null;
const deskIndex = $("desk-index-top");
const bottomIndex = $("desk-index-bottom");
bottomIndex.prepend(...Array.from(deskIndex.children, link => link.cloneNode(true)));
const indexLinks = [...deskIndex.children, ...bottomIndex.children];

function renderDeskIndex() {
  for (const link of indexLinks) {
    if (link.hasAttribute("data-focus-link")) {
      link.href = state.activeId ? "#state-heading" : "#draft-heading";
      link.textContent = state.activeId ? "眼前任务" : "开始任务";
    } else if (link.dataset.needs) {
      const section = $(link.dataset.needs);
      link.hidden = section.hidden || section.hasAttribute("data-empty");
    } else if (link.hasAttribute("data-review-link")) {
      link.hidden = !state.tasks.length;
    }
  }
}

function followIndex(event) {
  const link = event.target.closest("a");
  if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  const target = $(link.hash.slice(1));
  if (!target) return;
  event.preventDefault();
  if (link.hasAttribute("data-review-link") && !reviewOpen) {
    reviewOpen = true;
    renderReview();
  } else if (reviewOpen && matchMedia("(max-width: 759px)").matches &&
    link.matches("[data-work-link], [data-focus-link], [data-needs]")) {
    reviewOpen = false;
    renderReview();
  }
  if (target instanceof HTMLDetailsElement) target.open = true;
  const focusTarget = target.querySelector(":scope > summary") || target;
  target.scrollIntoView({ block: "start" });
  focusTarget.focus({ preventScroll: true });
}

deskIndex.addEventListener("click", followIndex);
bottomIndex.addEventListener("click", followIndex);

function newTask(title, step = "", parentId = null) {
  return {
    id: crypto.getRandomValues(new Uint32Array(4)).join("-"),
    title, step, note: "", parentId, status: step ? "working" : "queued",
  };
}

function storageNotice(message) {
  $("storage-notice").textContent = message;
  $("storage-notice").hidden = !message;
}

try {
  stored = localStorage.getItem(storageKey);
  if (stored !== null) {
    const saved = JSON.parse(stored);
    if (!Array.isArray(saved.tasks) || !Array.isArray(saved.thoughts) || !Array.isArray(saved.returnTrail)) {
      throw new Error("invalid saved tasks");
    }
    state = saved;
  } else {
    const legacy = JSON.parse(localStorage.getItem(legacyKey));
    if (Array.isArray(legacy?.thoughts)) state.thoughts = legacy.thoughts;
    if (legacy?.task) {
      const task = newTask(legacy.task.title, legacy.task.step);
      task.note = legacy.task.note || "";
      if (legacy.task.paused) task.status = "paused";
      state.activeId = task.id;
      state.tasks = [task];
    }
  }
} catch {
  storageNotice("无法读取保存的进度。请检查浏览器的存储设置。");
}

const changedElsewhere = "另一个标签页更新了进度。请先保留本页未保存的文字，再刷新以继续。";
window.addEventListener("storage", event => {
  if ((event.key === storageKey || event.key === null) && event.newValue !== stored) {
    storageNotice(changedElsewhere);
  }
});

function commit(next, message, updateView = render) {
  try {
    if (localStorage.getItem(storageKey) !== stored) {
      storageNotice(changedElsewhere);
      return false;
    }
    const serialized = JSON.stringify(next);
    localStorage.setItem(storageKey, serialized);
    stored = serialized;
    storageNotice("");
  } catch {
    storageNotice("浏览器无法保存进度。请检查存储设置或可用空间，再试一次。");
    return false;
  }
  state = next;
  if (message !== null) $("notice").textContent = message;
  updateView();
  return true;
}

function activeTask() {
  return state.tasks.find(task => task.id === state.activeId);
}

function taskWithEdits(task) {
  if (task.status === "step-done") {
    return {
      ...task, draft: undefined, nextDraft: $("next-step").value, result: $("task-result").value.trim(),
      nextExperiment: $("next-experiment").value.trim(),
    };
  }
  if (task.status !== "working") return task;
  return { ...task, draft: undefined, step: $("step").value.trim() || task.step, note: $("note").value.trim() };
}

function updateTask(task, message, updateView = render) {
  return commit({ ...state, tasks: state.tasks.map(item => item.id === task.id ? task : item) }, message, updateView);
}

function activate(task, message, { thoughts = state.thoughts, consumeStartDraft = false } = {}) {
  if (starting || task.id === state.activeId || task.status === "completed") return false;
  const current = activeTask();
  const edited = current && taskWithEdits(current);
  const next = { ...task, step: task.step || suggest(task.title) };
  if (next.status !== "step-done") next.status = "working";
  const tasks = state.tasks.map(item => {
    if (item.id === next.id) return next;
    if (item.id === edited?.id) {
      return { ...edited, status: edited.status === "working" ? "paused" : edited.status };
    }
    return item;
  });
  if (!tasks.some(item => item.id === next.id)) tasks.push(next);
  const returnTrail = state.returnTrail.filter(id => id !== next.id && id !== current?.id);
  if (current) returnTrail.push(current.id);
  const startDraft = consumeStartDraft ? "" : state.startDraft;
  if (commit({ ...state, tasks, activeId: next.id, returnTrail, thoughts, startDraft }, message)) {
    $(next.status === "step-done" ? "next-step" : "step").focus();
    return true;
  }
  return false;
}

function saveTask(input, parentId = null) {
  const title = input.value.trim();
  if (!title) return;
  const task = newTask(title, "", parentId);
  const tasks = [...state.tasks, task];
  const startDraft = input.id === "task" ? "" : state.startDraft;
  if (!commit({ ...state, tasks, startDraft }, parentId ? "子任务已存到任务树。" : "任务已存到待接回。", renderTasks)) return;
  input.value = "";
  if (input.id === "task") $("start-draft-status").textContent = "";
  return task;
}

const savedDraftMessage = "草稿已自动保存";
const unsavedDraftMessage = "草稿暂未保存";

function showDraftStatus(id, message) {
  const status = $(id);
  if (status.textContent !== message) status.textContent = message;
}

$("task").addEventListener("input", () => {
  if (state.activeId || starting) return;
  const startDraft = $("task").value;
  const saved = commit({ ...state, startDraft }, null, () => {});
  showDraftStatus("start-draft-status", saved ? (startDraft ? savedDraftMessage : "") : unsavedDraftMessage);
});

const taskDraftFields = {
  working: { step: "step", note: "note" },
  "step-done": { nextDraft: "next-step", result: "task-result", nextExperiment: "next-experiment" },
};
for (const field of Object.values(taskDraftFields).flatMap(fields => Object.values(fields))) {
  $(field).addEventListener("input", () => {
    const task = activeTask();
    const fields = taskDraftFields[task?.status];
    if (!fields) return;
    const draft = Object.fromEntries(Object.entries(fields).map(([key, id]) => [key, $(id).value]));
    const saved = updateTask({ ...task, draft }, null, () => {});
    showDraftStatus("task-draft-status", saved ? savedDraftMessage : unsavedDraftMessage);
  });
}

function render() {
  const task = activeTask();
  $("draft").hidden = !!task;
  $("current").hidden = !task;
  if (!task) {
    $("task").value = state.startDraft ?? "";
    $("start-draft-status").textContent = state.startDraft ? savedDraftMessage : "";
  }
  if (task) {
    const paused = task.status === "paused";
    const stepDone = task.status === "step-done";
    $("goal").textContent = task.title;
    $("state-heading").textContent = paused ? "暂停书签" : stepDone ? "这一小步做完了" : "眼前这一小步";
    $("step").value = task.draft?.step ?? task.step;
    $("step").readOnly = paused;
    $("step-form").hidden = stepDone;
    $("step-actions").hidden = paused;
    $("note").value = task.draft?.note ?? task.note;
    $("pause-form").hidden = paused || stepDone;
    $("return-note").textContent = task.note ? "回来时：" + task.note : "";
    $("return-note").hidden = !task.note || stepDone;
    $("resume").hidden = !paused;
    $("park-task").hidden = !paused;
    $("done").hidden = paused || stepDone;
    $("next-form").hidden = !stepDone;
    $("next-step").value = task.draft?.nextDraft ?? task.nextDraft ?? "";
    $("result-box").hidden = !stepDone;
    $("task-result").value = task.draft?.result ?? task.result ?? "";
    $("next-experiment").value = task.draft?.nextExperiment ?? task.nextExperiment ?? "";
    $("result-box").open = stepDone && !!($("task-result").value || $("next-experiment").value);
    $("task-draft-status").textContent = task.draft ? savedDraftMessage : "";
    $("finish-task").hidden = !stepDone;
  }
  renderDistractionLog();
  renderTasks();
  renderShelf();
}

function renderDistractionLog() {
  const task = activeTask();
  const id = task?.id ?? null;
  const box = $("distraction-box");
  if (id !== distractionTaskId) {
    $("distraction-reason").value = "";
    box.open = false;
    distractionTaskId = id;
  }
  box.hidden = task?.status !== "working";
  const count = task?.distractions?.length ?? 0;
  $("distraction-count").textContent = count ? "已记 " + count + " 次" : "";
  $("undo-distraction").hidden = !count;
}

function rowButton(text, label, action) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "quiet";
  button.textContent = text;
  button.setAttribute("aria-label", label);
  button.onclick = action;
  return button;
}

function openSavedTask(task) {
  return activate(task, task.status === "queued" ? "已开始这件事。" : "从上次停下的地方接着来。");
}

function removeTask(task, focusTarget) {
  if (!window.confirm("移除「" + task.title + "」及其记录？")) return;
  const tasks = state.tasks.filter(item => item.id !== task.id);
  const returnTrail = state.returnTrail.filter(id => id !== task.id);
  if (commit({ ...state, tasks, returnTrail }, "任务已移除。", renderTasks)) {
    expandedTasks.delete(task.id);
    childDrafts.delete(task.id);
    (focusTarget.hidden || !state.tasks.length ? $("task") : focusTarget).focus();
  }
}

function renderTasks() {
  renderRecap();
  const current = activeTask();
  const saved = state.tasks.filter(task => task.id !== state.activeId && task.status !== "completed");
  const returnTask = !current && saved.find(task => task.id === state.returnTrail.at(-1));
  const listed = saved.filter(task => task.id !== returnTask?.id);
  $("task-shelf").toggleAttribute("data-empty", !state.tasks.length);
  $("tree-toggle").hidden = !state.tasks.length;
  renderDeskIndex();
  $("add-task").hidden = !current;
  $("task-count").textContent = listed.length ? `${listed.length} 件` : "";
  $("tree-toggle").textContent = treeOpen ? "返回列表" : "任务树";
  $("tree-toggle").setAttribute("aria-expanded", String(treeOpen));
  $("task-tree").hidden = !treeOpen;
  $("saved-tasks").hidden = treeOpen;
  $("shelf-empty").hidden = treeOpen || !!listed.length || !!current;
  $("return-prompt").hidden = !returnTask;
  $("return-title").textContent = returnTask ? returnTask.title : "";
  $("return-context").textContent = returnTask?.status === "step-done" ? "上一步已完成" :
    returnTask?.note || returnTask?.step || "";
  $("return-task").disabled = starting;
  $("return-task").onclick = returnTask ? () => activate(returnTask, "从上次停下的地方接着来。") : null;
  renderReview();
  if (treeOpen) {
    renderTaskTree();
    return;
  }
  $("saved-tasks").replaceChildren(...listed.map(task => {
    const item = document.createElement("li");
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = task.title;
    const detail = document.createElement("p");
    detail.textContent = task.status === "queued" ? "还没开始" :
      task.status === "step-done" ? "上一步已完成" : task.note || task.step;
    copy.append(title, detail);
    const actions = document.createElement("div");
    actions.className = "actions";
    const text = task.status === "queued" ? "开始" : "接回来";
    const open = rowButton(text, text + "：" + task.title, () => openSavedTask(task));
    open.disabled = starting;
    const remove = rowButton("移除", "移除任务：" + task.title, () => {
      removeTask(task, current ? $("add-task").querySelector("summary") : $("task"));
    });
    actions.append(open, remove);
    item.append(copy, actions);
    return item;
  }));
}

function taskStatus(task) {
  if (task.status === "completed") return "已完成";
  if (task.status === "queued") return "待开始";
  if (task.status === "step-done") return "上一步已完成";
  if (task.status === "paused") return "已暂停";
  return "进行中";
}

function taskFields(task) {
  const completed = task.status === "completed";
  const completedSteps = task.completedSteps ?? [];
  return [
    ["已完成的小步", completedSteps],
    [completed ? "最后一步" : "保存的步骤", completed && completedSteps.length ? "" : task.step],
    ["返回提示", completed ? "" : task.note],
    ["结果", completed ? task.result : ""],
    ...distractionFields(task),
    ["下次试试", completed ? task.nextExperiment : ""],
  ];
}

function distractionFields(task) {
  const reasons = task.distractions ?? [];
  if (!reasons.length && task.status !== "completed") return [];
  const fields = [["分神记录", reasons.length ? "记下 " + reasons.length + " 次" : "这件事没有分神记录。"]];
  if (!reasons.length) return fields;
  const counts = new Map();
  for (const reason of reasons) counts.set(reason, (counts.get(reason) ?? 0) + 1);
  const byFrequency = [...counts].sort((a, b) => b[1] - a[1]);
  fields.push(["当时记下的原因", byFrequency.map(([reason, count]) =>
    (reason || "未填原因") + " × " + count).join("\n")]);
  return fields;
}

function renderRecap() {
  if (state.activeId) recapId = null;
  const task = state.tasks.find(item => item.id === recapId);
  $("task-recap").hidden = !task;
  if (!task) return;
  $("recap-title").textContent = task.title;
  const fields = $("recap-fields");
  fields.replaceChildren();
  appendFields(fields, taskFields(task));
}

function appendFields(container, entries) {
  const fields = document.createElement("dl");
  for (const [label, text] of entries) {
    if (!text || (Array.isArray(text) && !text.length)) continue;
    const term = document.createElement("dt");
    term.textContent = label;
    const value = document.createElement("dd");
    if (Array.isArray(text)) {
      const list = document.createElement("ol");
      list.className = "completed-steps";
      for (const step of text) {
        const item = document.createElement("li");
        item.textContent = step;
        list.append(item);
      }
      value.append(list);
    } else {
      value.textContent = text;
    }
    fields.append(term, value);
  }
  if (fields.childElementCount) container.append(fields);
}

function renderReviewDetail(task) {
  const detail = $("review-detail");
  detail.replaceChildren();
  const status = document.createElement("p");
  status.className = "optional";
  const parent = state.tasks.find(item => item.id === task.parentId);
  status.textContent = [taskStatus(task), parent && "来自「" + parent.title + "」"].filter(Boolean).join(" · ");
  detail.append(status);
  appendFields(detail, taskFields(task));
  if (task.status === "completed" || task.id === state.activeId) return;
  const text = task.status === "queued" ? "开始这件事" : "接回来";
  const open = rowButton(text, text + "：" + task.title, () => {
    if (!openSavedTask(task) || !matchMedia("(max-width: 759px)").matches) return;
    reviewOpen = false;
    renderReview();
    $(task.status === "step-done" ? "next-step" : "step").focus();
  });
  open.disabled = starting;
  detail.append(open);
}

function summaryFields(task) {
  const completed = task.status === "completed";
  const stepDone = task.status === "step-done";
  let position = task.note || "已保存当前步骤。";
  let next = task.step || "开始时会给出第一步。";
  if (completed) {
    position = task.step || "任务已结束。";
    next = "已完成。";
  } else if (stepDone) {
    position = task.step ? "已完成这一步：" + task.step : "上一步已完成。";
    next = task.nextDraft?.trim() || "还没写下一步。";
  } else if (task.status === "queued") {
    position = "还没开始。";
  }
  return [
    ["已完成的小步", task.completedSteps ?? []],
    ["已记录的结果", (completed && task.result) || "还没写结果。"],
    ["停在这里", position],
    ["下一步", next],
    ...distractionFields(task),
    ["下次试试", completed ? task.nextExperiment : ""],
  ];
}

function renderSummary() {
  const tasks = state.tasks.filter(task => summarizedIds.includes(task.id));
  $("summary-result").hidden = !tasks.length;
  $("summary-items").replaceChildren(...tasks.map(task => {
    const item = document.createElement("li");
    const title = document.createElement("h4");
    title.textContent = task.title;
    const status = document.createElement("p");
    status.className = "optional";
    status.textContent = taskStatus(task);
    item.append(title, status);
    appendFields(item, summaryFields(task));
    item.append(rowButton("查看来源", "查看来源：" + task.title, () => {
      reviewId = task.id;
      $("review-task").value = reviewId;
      renderReviewDetail(task);
      $("review-task").focus();
    }));
    return item;
  }));
}

function renderReview() {
  if (!state.tasks.length) reviewOpen = false;
  document.querySelector("main").classList.toggle("review-open", reviewOpen);
  $("review-toggle").hidden = !state.tasks.length;
  $("review-toggle").textContent = reviewOpen ? "关闭回看" : "回看任务";
  $("review-toggle").setAttribute("aria-expanded", String(reviewOpen));
  $("task-review").hidden = !reviewOpen;
  if (!reviewOpen) return;

  const task = state.tasks.find(item => item.id === reviewId) ||
    state.tasks.find(item => item.id !== state.activeId) || state.tasks[0];
  reviewId = task.id;
  $("review-task").replaceChildren(...state.tasks.map(item => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.title + "（" + taskStatus(item) + "）";
    return option;
  }));
  $("review-task").value = reviewId;
  renderReviewDetail(task);

  const existingIds = new Set(state.tasks.map(item => item.id));
  for (const id of summarySelection) if (!existingIds.has(id)) summarySelection.delete(id);
  summarizedIds = summarizedIds.filter(id => existingIds.has(id));
  $("summary-choices").replaceChildren(...state.tasks.map(item => {
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = summarySelection.has(item.id);
    checkbox.onchange = () => {
      if (checkbox.checked) summarySelection.add(item.id);
      else summarySelection.delete(item.id);
      $("generate-summary").disabled = !summarySelection.size;
    };
    const copy = document.createElement("span");
    copy.textContent = item.title + "（" + taskStatus(item) + "）";
    label.append(checkbox, copy);
    return label;
  }));
  $("generate-summary").disabled = !summarySelection.size;
  renderSummary();
}

function showReview(taskId = reviewId) {
  reviewId = taskId;
  reviewOpen = true;
  renderReview();
  $("review-heading").focus();
}

$("review-toggle").onclick = () => {
  if (!reviewOpen) return showReview();
  reviewOpen = false;
  renderReview();
};
$("review-task").onchange = event => {
  reviewId = event.target.value;
  const task = state.tasks.find(item => item.id === reviewId);
  if (task) renderReviewDetail(task);
};
submit("summary-form", () => {
  if (!summarySelection.size) return;
  summarizedIds = [...summarySelection];
  renderSummary();
  $("summary-heading").focus();
});

function childTaskForm(task) {
  const details = document.createElement("details");
  details.className = "child-form";
  details.open = childDrafts.has(task.id);
  const summary = document.createElement("summary");
  summary.textContent = "添加子任务";
  const form = document.createElement("form");
  const label = document.createElement("label");
  label.htmlFor = "child-" + task.id;
  label.textContent = "子任务叫什么？";
  const input = document.createElement("input");
  input.id = label.htmlFor;
  input.required = true;
  input.maxLength = 500;
  input.value = childDrafts.get(task.id) || "";
  input.oninput = () => childDrafts.set(task.id, input.value);
  const save = document.createElement("button");
  save.className = "quiet";
  save.textContent = "保存子任务";
  form.onsubmit = event => {
    event.preventDefault();
    const draft = childDrafts.get(task.id);
    childDrafts.delete(task.id);
    const added = saveTask(input, task.id);
    if (added) $("tree-node-" + added.id)?.focus();
    else if (draft !== undefined) childDrafts.set(task.id, draft);
  };
  form.append(label, input, save);
  details.append(summary, form);
  return details;
}

function renderTaskTree() {
  const byId = new Map(state.tasks.map(task => [task.id, task]));
  const children = new Map();
  for (const task of state.tasks) {
    const parent = task.parentId !== task.id && byId.has(task.parentId) ? task.parentId : null;
    if (!children.has(parent)) children.set(parent, []);
    children.get(parent).push(task);
  }

  if (treeActiveId !== state.activeId) {
    const path = new Set();
    for (let task = byId.get(state.activeId); task && !path.has(task.id); task = byId.get(task.parentId)) {
      path.add(task.id);
      expandedTasks.add(task.id);
    }
    treeActiveId = state.activeId;
  }

  function node(task, depth) {
    const current = task.id === state.activeId;
    const completed = task.status === "completed";
    const item = document.createElement("li");
    item.className = "tree-item";
    const button = document.createElement("button");
    button.type = "button";
    button.id = "tree-node-" + task.id;
    button.className = "tree-node quiet";
    const title = document.createElement("span");
    title.textContent = task.title;
    const status = document.createElement("span");
    status.className = "tree-status";
    status.textContent = (current ? "眼前 · " : "") + taskStatus(task);
    if (current) button.setAttribute("aria-current", "true");
    button.append(title, status);

    const branch = document.createElement("div");
    branch.id = "tree-branch-" + task.id;
    branch.className = "tree-branch";
    button.setAttribute("aria-controls", branch.id);
    function setOpen(open) {
      branch.hidden = !open;
      button.setAttribute("aria-expanded", String(open));
      if (open) expandedTasks.add(task.id);
      else expandedTasks.delete(task.id);
    }
    setOpen(expandedTasks.has(task.id));
    button.onclick = () => setOpen(branch.hidden);

    const preview = document.createElement("div");
    preview.className = "tree-preview";
    appendFields(preview, taskFields(task));
    const actions = document.createElement("div");
    actions.className = "actions";
    actions.append(rowButton("回看", "回看：" + task.title, () => showReview(task.id)));
    if (!current && !completed) {
      const text = task.status === "queued" ? "开始" : "接回来";
      const open = rowButton(text, text + "：" + task.title, () => openSavedTask(task));
      open.disabled = starting;
      actions.append(open);
    }
    if (!current) {
      actions.append(rowButton("移除", "移除任务：" + task.title, () => removeTask(task, $("tree-toggle"))));
    }
    if (actions.childElementCount) preview.append(actions);
    if (!completed) preview.append(childTaskForm(task));
    branch.append(preview);
    if (children.has(task.id)) {
      const list = document.createElement("ul");
      list.className = depth < 4 ? "tree-children" : "tree-children tree-deep";
      list.append(...children.get(task.id).map(child => node(child, depth + 1)));
      branch.append(list);
    }
    item.append(button, branch);
    return item;
  }

  $("task-tree").replaceChildren(...(children.get(null) || []).map(task => node(task, 0)));
}

$("tree-toggle").onclick = () => {
  treeOpen = !treeOpen;
  if (treeOpen) treeActiveId = null;
  renderTasks();
};

function renderShelf() {
  $("thoughts").replaceChildren(...state.thoughts.map((thought, index) => {
    const item = document.createElement("li");
    const label = document.createElement("span");
    label.textContent = thought;
    const remaining = () => state.thoughts.filter((_, position) => position !== index);
    const start = rowButton("先做这件", "先做这件：" + thought, () => {
      const parentId = state.activeId;
      activate(newTask(thought, "", parentId), parentId ? "原任务已留在待接回。" : "已开始这件事。", {
        thoughts: remaining(),
      });
    });
    start.disabled = starting;
    const clear = rowButton("移除", "移除暂存事项：" + thought, () => {
      if (commit({ ...state, thoughts: remaining() }, "已移除暂存事项。", renderShelf)) $("thought").focus();
    });
    const actions = document.createElement("div");
    actions.className = "actions";
    actions.append(start, clear);
    item.append(label, actions);
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
  if (!title || starting || activeTask()) return;
  const config = ai;
  let step = suggest(title);
  let message = "已找到一个起点。";
  if (config) {
    const button = $("start-task");
    starting = true;
    button.disabled = true;
    $("save-task").disabled = true;
    $("task").readOnly = true;
    button.textContent = "正在找第一步…";
    $("notice").textContent = "正在连接 AI 接口。";
    renderTasks();
    renderShelf();
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
      $("save-task").disabled = false;
      $("task").readOnly = false;
      button.textContent = "出发咯";
      $("notice").textContent = "";
      renderTasks();
      renderShelf();
    }
  }
  activate(newTask(title, step), message, { consumeStartDraft: true });
});
$("save-task").onclick = () => {
  if (!starting && !activeTask()) saveTask($("task"));
};
submit("queue-form", () => saveTask($("queued-task")));
submit("step-form", () => {
  const task = activeTask();
  if (task?.status !== "working" || !$("step").value.trim()) return;
  updateTask(taskWithEdits(task), "步骤已保存。");
});
submit("pause-form", () => {
  const task = activeTask();
  if (task?.status !== "working") return;
  if (updateTask({ ...taskWithEdits(task), status: "paused" }, "书签已保存。")) $("resume").focus();
});
$("resume").onclick = () => {
  const task = activeTask();
  if (task?.status !== "paused") return;
  if (updateTask({ ...task, status: "working" }, "从这里接着来。")) $("step").focus();
};
$("park-task").onclick = () => {
  const task = activeTask();
  if (task?.status !== "paused") return;
  const returnTrail = [...state.returnTrail.filter(id => id !== task.id), task.id];
  if (commit({ ...state, activeId: null, returnTrail }, "书签已留在待接回。")) $("task").focus();
};
$("done").onclick = () => {
  const task = activeTask();
  if (task?.status !== "working") return;
  const edited = taskWithEdits(task);
  const completedSteps = [...(task.completedSteps ?? []), edited.step];
  if (updateTask({ ...edited, completedSteps, status: "step-done" }, "这一步完成了。")) $("next-step").focus();
};
submit("next-form", () => {
  const task = activeTask();
  const step = $("next-step").value.trim();
  if (task?.status !== "step-done" || !step) return;
  const next = { ...taskWithEdits(task), step, note: "", nextDraft: "", status: "working" };
  if (updateTask(next, "下一步已保存。")) $("step").focus();
});
$("finish-task").onclick = () => {
  const task = activeTask();
  if (task?.status !== "step-done") return;
  const finished = {
    ...taskWithEdits(task), status: "completed", nextDraft: "", completedAt: new Date().toISOString(),
  };
  const tasks = state.tasks.map(item => item.id === task.id ? finished : item);
  const returnTrail = state.returnTrail.filter(id => id !== task.id);
  if (commit({ ...state, activeId: null, tasks, returnTrail }, "任务已完成，回顾已保存。")) {
    recapId = task.id;
    renderRecap();
    renderDeskIndex();
    $("recap-heading").focus();
  }
};
$("recap-close").onclick = () => {
  recapId = null;
  renderRecap();
  renderDeskIndex();
  ($("return-prompt").hidden ? $("task") : $("return-task")).focus();
};
submit("distraction-form", () => {
  const input = $("distraction-reason");
  if (recordDistraction(input.value.trim())) input.value = "";
});
$("distraction-shortcuts").addEventListener("click", event => {
  const shortcut = event.target.closest("button[data-reason]");
  if (shortcut) recordDistraction(shortcut.dataset.reason);
});
function recordDistraction(reason) {
  const task = activeTask();
  if (task?.status !== "working") return false;
  const distractions = [...(task.distractions ?? []), reason];
  return saveDistractions(task, distractions, "已记下一次分神。");
}
$("undo-distraction").onclick = () => {
  const task = activeTask();
  if (task?.status !== "working" || !task.distractions?.length) return;
  if (saveDistractions(task, task.distractions.slice(0, -1), "已撤销上一次记录。")) {
    $("distraction-reason").focus();
  }
};
function saveDistractions(task, distractions, message) {
  return updateTask({ ...task, distractions }, message, () => {
    renderDistractionLog();
    renderTasks();
  });
}
submit("capture", () => {
  const thought = $("thought").value.trim();
  if (!thought) return;
  const thoughts = [...state.thoughts, thought];
  if (commit({ ...state, thoughts }, "念头已暂存。", renderShelf)) $("thought").value = "";
});
render();
