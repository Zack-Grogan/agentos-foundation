"use strict";
const $ = (id) => document.getElementById(id);
let state,
  csrf,
  opener,
  busy = false;
let captureRequest = null;
const draftRequests = new Map();
const dialog = $("inspector");
const captureDialog = $("capture-dialog");
$("new-capture").onclick = () => {
  captureDialog.showModal();
  $("title").focus();
};
function closeCapture() {
  captureDialog.close();
  $("new-capture").focus();
}
$("close-capture").onclick = closeCapture;
captureDialog.addEventListener("cancel", (e) => {
  e.preventDefault();
  closeCapture();
});
function el(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
let noticeTimer;
function note(text) {
  clearTimeout(noticeTimer);
  $("notice").textContent = text;
  if (!/failed|stale|could not|unavailable|retry/i.test(text))
    noticeTimer = setTimeout(() => {
      $("notice").textContent = "";
    }, 6000);
}
function remember(key, value) {
  try {
    localStorage.setItem("agentos." + key, JSON.stringify(value));
  } catch {
    note(
      "Browser preferences could not be saved. Your workspace records are unaffected.",
    );
  }
}
function recalled(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem("agentos." + key)) ?? fallback;
  } catch {
    return fallback;
  }
}
function date(value) {
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
async function api(path, data) {
  const response = await fetch(path, {
    method: data ? "POST" : "GET",
    headers: data
      ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
      : {},
    body: data ? JSON.stringify(data) : undefined,
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed.");
  return result;
}
async function refresh() {
  try {
    state = await api("/api/state");
    render();
  } catch (error) {
    note(error.message + " Displayed records may be stale.");
    throw error;
  }
}
function empty(parent, text) {
  const p = el("p", undefined, "empty");
  p.append(el("span", "◇", "empty-symbol"), document.createTextNode(text));
  parent.append(p);
}
function button(text, fn, cls) {
  const b = el("button", text, cls);
  b.type = "button";
  b.addEventListener("click", fn);
  return b;
}
function record(parent, title, detail, fn) {
  const b = button("", fn, "record");
  b.append(el("strong", title), el("small", detail));
  parent.append(b);
}
function open(title, type) {
  opener = document.activeElement;
  $("inspector-title").textContent = title;
  $("inspector-type").textContent = type;
  $("inspector-body").replaceChildren();
  if (!dialog.open) dialog.showModal();
  $("close-inspector").focus();
  return $("inspector-body");
}
function close() {
  dialog.close();
  if (opener?.isConnected) opener.focus();
}
$("close-inspector").onclick = close;
dialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  close();
});
for (const focusDialog of [dialog, captureDialog])
  focusDialog.addEventListener("keydown", (event) => {
    if (event.key !== "Tab") return;
    const focusable = [
      ...focusDialog.querySelectorAll(
        'button:not(:disabled),a[href],input,textarea,select,[tabindex="0"]',
      ),
    ].filter((e) => !e.hidden && e.getClientRects().length);
    const first = focusable[0],
      last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  });
async function mutate(fn) {
  if (busy) return;
  busy = true;
  const controls = [
    ...document.querySelectorAll('button[type="submit"],.mutation'),
  ];
  controls.forEach((b) => (b.disabled = true));
  try {
    await fn();
    await refresh();
  } catch (error) {
    note(error.message + " Review the recorded state before retrying.");
  } finally {
    busy = false;
    controls.forEach((b) => (b.disabled = false));
  }
}
function render() {
  const pending = state.artifacts.filter((a) => a.review === "pending");
  $("strip-sources").textContent = state.sources.length;
  $("strip-reviews").textContent = pending.length;
  $("strip-projects").textContent = state.projects.length;
  $("center-readout").textContent = pending.length
    ? pending.length + " awaiting review"
    : "No pending drafts";
  $("source-count").textContent = state.sources.length + " captured";
  $("draft-count").textContent = state.artifacts.length + " created";
  $("project-count").textContent = state.projects.length + " accepted";
  $("run-count").textContent = state.runs.length + " recorded";
  $("review-count").textContent = pending.length + " PENDING";
  $("reviews").replaceChildren();
  if (!pending.length)
    empty(
      $("reviews"),
      "Nothing waiting on you. Draft a plan from a captured source to begin.",
    );
  pending
    .slice(0, 4)
    .forEach((a) =>
      record(
        $("reviews"),
        a.content.title,
        "Draft · validation passed · inspect →",
        () => showArtifact(a.id),
      ),
    );
  renderSources();
  $("activity").replaceChildren();
  if (!state.events.length)
    empty(
      $("activity"),
      "Your first capture will appear here. No fabricated activity.",
    );
  state.events.slice(0, 4).forEach((e) => {
    const row = el("div", undefined, "event");
    row.append(
      el("span", e.kind.replaceAll(".", " · ")),
      el("time", date(e.at)),
    );
    $("activity").append(row);
  });
  $("as-of").textContent = date(state.as_of);
}
function renderSources() {
  const q = $("search").value.toLowerCase();
  $("sources").replaceChildren();
  const rows = state.sources.filter((s) =>
    (s.title + " " + s.body).toLowerCase().includes(q),
  );
  if (!rows.length)
    empty(
      $("sources"),
      q
        ? "No sources match this search."
        : "Your captured inputs will live here, linked to the work they inform.",
    );
  rows
    .slice(0, 8)
    .forEach((s) =>
      record(
        $("sources"),
        s.title,
        "Captured " + date(s.observed_at) + " · open source →",
        () => showSource(s.id),
      ),
    );
}
function showSource(id) {
  const s = state.sources.find((s) => s.id === id);
  if (!s) return;
  const body = open(s.title, "SOURCE · REVISION " + s.revision);
  body.append(
    el("p", "Captured " + date(s.observed_at), "muted"),
    el("pre", s.body),
    el("h3", "Source identity"),
    el("p", s.digest, "footnote"),
  );
  const b = button(
    "Create plan draft",
    () =>
      mutate(async () => {
        if (!draftRequests.has(id)) draftRequests.set(id, crypto.randomUUID());
        const a = await api("/api/draft", {
          source_id: id,
          request_id: draftRequests.get(id),
        });
        draftRequests.delete(id);
        await refresh();
        showArtifact(a.id);
        note(
          "Draft created from the selected source. Review it before accepting.",
        );
      }),
    "primary mutation",
  );
  body.append(b);
}
function showArtifact(id) {
  const a = state.artifacts.find((a) => a.id === id);
  if (!a) return;
  const body = open(a.content.title, "DRAFT · " + a.review.toUpperCase());
  body.append(
    el("p", "Deterministic reference · validation " + a.validation, "muted"),
    el("h3", "Source objective"),
    el("pre", a.content.objective),
    el("h3", "Proposed next actions"),
  );
  const list = el("ol");
  a.content.next_actions.forEach((t) => list.append(el("li", t)));
  body.append(
    list,
    el("h3", "Assumption"),
    el("p", a.content.assumptions.join(" ")),
    el("h3", "Open question"),
    el("p", a.content.questions.join(" ")),
    el("h3", "Evidence"),
    el(
      "p",
      "Run " + a.run_id + " · artifact revision " + a.revision,
      "footnote",
    ),
  );
  const actions = el("div", undefined, "actions");
  actions.append(
    button("Inspect source", () => showSource(a.content.source_id)),
  );
  if (a.review === "pending")
    for (const [decision, label] of [
      ["accepted", "Accept as local project"],
      ["rejected", "Reject draft"],
    ])
      actions.append(
        button(
          label,
          () =>
            mutate(async () => {
              await api("/api/review", {
                artifact_id: a.id,
                expected_digest: a.digest,
                decision,
              });
              await refresh();
              showArtifact(a.id);
              note(
                decision === "accepted"
                  ? "Project created. Its tasks remain proposed."
                  : "Draft rejected and preserved.",
              );
            }),
          decision === "accepted" ? "primary mutation" : "mutation",
        ),
      );
  if (a.project_id)
    actions.append(
      button(
        "Open accepted project",
        () => showProject(a.project_id),
        "primary",
      ),
    );
  body.append(actions);
}
function showProject(id) {
  const p = state.projects.find((p) => p.id === id);
  if (!p) return;
  const body = open(p.title, "ACCEPTED LOCAL PROJECT");
  body.append(el("pre", p.objective), el("h3", "Proposed tasks"));
  p.tasks.forEach((t) => body.append(el("p", "○ " + t.title)));
  body.append(
    el("p", "No task has been executed by this reference.", "muted"),
    button("Inspect original draft", () => showArtifact(p.artifact_id)),
  );
}
function collection(kind) {
  const body = open(
    {
      sources: "Source library",
      artifacts: "Draft library",
      projects: "Accepted projects",
      runs: "Recorded runs",
    }[kind],
    "WORKSPACE",
  );
  const rows = state[kind];
  if (!rows.length)
    empty(body, "No records yet. Capture one useful input to begin.");
  rows.forEach((r) => {
    if (kind === "runs") {
      record(body, r.skill, r.status + " · " + date(r.finished_at), () =>
        showArtifact(r.artifact_id),
      );
    } else
      record(
        body,
        r.title ?? r.content.title,
        kind === "artifacts" ? r.review : "Open record →",
        () =>
          ({
            sources: showSource,
            artifacts: showArtifact,
            projects: showProject,
          })[kind](r.id),
      );
  });
}
document
  .querySelectorAll("[data-collection]")
  .forEach((b) => (b.onclick = () => collection(b.dataset.collection)));
$("search").oninput = renderSources;
$("capture-form").onsubmit = (event) => {
  event.preventDefault();
  mutate(async () => {
    const title = $("title").value,
      body = $("body").value;
    const fingerprint = JSON.stringify([title, body]);
    if (captureRequest?.fingerprint !== fingerprint)
      captureRequest = { fingerprint, id: crypto.randomUUID() };
    const source = await api("/api/capture", {
      title,
      body,
      request_id: captureRequest.id,
    });
    captureRequest = null;
    $("capture-form").reset();
    remember("capture", null);
    await refresh();
    captureDialog.close();
    showSource(source.id);
    note("Source saved. Create a draft when you are ready.");
  });
};
for (const id of ["title", "body"])
  $(id).oninput = () =>
    remember("capture", { title: $("title").value, body: $("body").value });
const saved = recalled("capture", null);
if (
  saved &&
  typeof saved.title === "string" &&
  typeof saved.body === "string"
) {
  $("title").value = saved.title;
  $("body").value = saved.body;
}
function view(list) {
  $("orbit").classList.toggle("list", list);
  $("view-mode").textContent = list ? "Map view" : "List view";
  $("view-mode").setAttribute("aria-pressed", String(list));
  remember("list", list);
}
$("view-mode").onclick = () => view(!$("orbit").classList.contains("list"));
view(recalled("list", false) === true);
function applyLayout() {
  const layout = recalled("layout", {});
  for (const id of ["sources-panel", "activity-panel"])
    $(id).hidden = layout[id] === false;
  $("review-panel").classList.toggle("before", layout.reviewFirst === true);
  $("capture-panel").classList.toggle("after", layout.reviewFirst === true);
}
$("arrange").onclick = () => {
  const body = open("Arrange your workspace", "PRESENTATION ONLY");
  body.append(
    el(
      "p",
      "Layout controls change presentation. They never change your sources or accepted work.",
    ),
  );
  for (const [id, label] of [
    ["sources-panel", "Source library"],
    ["activity-panel", "Run history"],
  ]) {
    const row = el("div", undefined, "widget-controls");
    const toggle = button($(id).hidden ? "Show" : "Hide", () => {
      const layout = recalled("layout", {});
      layout[id] = $(id).hidden;
      remember("layout", layout);
      applyLayout();
      toggle.textContent = $(id).hidden ? "Show" : "Hide";
    });
    row.append(el("span", label), toggle);
    body.append(row);
  }
  const row = el("div", undefined, "actions");
  row.append(
    button("Swap side instruments", () => {
      const l = recalled("layout", {});
      l.reviewFirst = !l.reviewFirst;
      remember("layout", l);
      applyLayout();
    }),
    button("Restore layout", () => {
      remember("layout", {});
      applyLayout();
      close();
    }),
  );
  body.append(row);
};
applyLayout();
$("guide-button").onclick = () => {
  const body = open("A small system that works", "ARMS WORKSPACE GUIDE");
  for (const [title, text] of [
    [
      "Applications",
      "This reference reads and writes its local records. No external account is connected.",
    ],
    [
      "Routines",
      "Scheduling is off. The playbook describes the bounded runner extension.",
    ],
    [
      "Memory",
      "Captured sources, drafts, accepted projects and run events persist in SQLite.",
    ],
    [
      "Skills",
      "Capture-to-plan produces a deterministic scaffold for review. Replace it with a tested agent adapter when ready.",
    ],
  ])
    body.append(el("h3", title), el("p", text));
  body.append(
    el(
      "p",
      "This guide occupies the future assistant surface. It is documentation, not a simulated chat.",
      "muted",
    ),
  );
};
$("refresh").onclick = () =>
  refresh()
    .then(() => note("Records refreshed."))
    .catch(() => {});
(async () => {
  try {
    csrf = (await api("/api/session")).csrf;
    await refresh();
  } catch (e) {
    note(e.message);
  }
})();
