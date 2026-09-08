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
    localStorage.setItem(
      "agentos." + (state?.workspace_id || "pending") + "." + key,
      JSON.stringify(value),
    );
  } catch {
    note(
      "Browser preferences could not be saved. Your workspace records are unaffected.",
    );
  }
}
function recalled(key, fallback) {
  try {
    return (
      JSON.parse(
        localStorage.getItem(
          "agentos." + (state?.workspace_id || "pending") + "." + key,
        ),
      ) ?? fallback
    );
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
let currentRoute = null,
  routeStack = [];
function open(title, type, route = null) {
  if (route && currentRoute && route !== currentRoute)
    routeStack.push({
      route: currentRoute,
      scroll: $("inspector-body").scrollTop,
    });
  currentRoute = route;
  $("inspector-back").hidden = routeStack.length === 0;
  if (!dialog.open) opener = document.activeElement;
  $("inspector-title").textContent = title;
  $("inspector-type").textContent = type;
  $("inspector-body").replaceChildren();
  if (!dialog.open) dialog.showModal();
  $("close-inspector").focus();
  return $("inspector-body");
}
function close() {
  dialog.close();
  currentRoute = null;
  routeStack = [];
  if (opener?.isConnected) opener.focus();
}
$("close-inspector").onclick = close;
dialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  close();
});
for (const focusDialog of [dialog, captureDialog])
  focusDialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !event.isComposing) {
      event.preventDefault();
      if (focusDialog === dialog) close();
      else closeCapture();
      return;
    }
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
  applyLayout();
  renderDomain();
  $("routine-control").textContent = state.scheduler_active
    ? "● Scheduler on"
    : "● Scheduler off";
  document.querySelector(".strip-mode").textContent = state.providers.some(
    (p) => p.enabled && p.id !== "local",
  )
    ? "Providers configured · select per run"
    : "Local planner · no external provider";
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
  const body = open(s.title, "SOURCE · REVISION " + s.revision, "source:" + id);
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
  const controls = el("div", undefined, "actions");
  const provider = el("select");
  provider.setAttribute("aria-label", "Run provider");
  state.providers
    .filter((p) => p.enabled)
    .forEach((p) => {
      const option = el("option", p.id + " · " + p.status);
      option.value = p.id;
      provider.append(option);
    });
  controls.append(
    provider,
    button(
      "Run skill",
      () =>
        mutate(async () => {
          const key = "job:" + id + ":" + provider.value;
          if (!draftRequests.has(key))
            draftRequests.set(key, crypto.randomUUID());
          const job = await api("/api/jobs", {
            source_id: id,
            request_id: draftRequests.get(key),
            provider_id: provider.value,
          });
          draftRequests.delete(key);
          await refresh();
          showJob(job.id);
        }),
      "mutation",
    ),
    button("Edit source", () => editSource(id)),
    button("Create routine", () => createRoutine(id, provider.value)),
  );
  body.append(controls);
}
function showArtifact(id) {
  const a = state.artifacts.find((a) => a.id === id);
  if (!a) return;
  const body = open(
    a.content.title,
    "DRAFT · " + a.review.toUpperCase(),
    "artifact:" + id,
  );
  body.append(
    el(
      "p",
      (a.provider && !["local", "deterministic-reference"].includes(a.provider)
        ? a.provider
        : "Deterministic reference") +
        " · validation " +
        a.validation,
      "muted",
    ),
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
  const body = open(p.title, "ACCEPTED LOCAL PROJECT", "project:" + id);
  body.append(el("pre", p.objective), el("h3", "Proposed tasks"));
  p.tasks.forEach((t, index) => {
    const row = el("div", undefined, "task-row");
    const select = el("select");
    select.setAttribute("aria-label", "Status: " + t.title);
    for (const status of ["proposed", "in_progress", "done"]) {
      const option = el("option", status.replaceAll("_", " "));
      option.value = status;
      select.append(option);
    }
    select.value = t.status;
    select.onchange = () =>
      mutate(async () => {
        await api("/api/task", {
          project_id: id,
          revision: p.revision || 1,
          index,
          status: select.value,
        });
        await refresh();
        if (dialog.open && currentRoute === "project:" + id) showProject(id);
      });
    row.append(el("span", t.title), select);
    body.append(row);
  });
  body.append(
    el(
      "p",
      "Task status records your progress. No external action is executed.",
      "muted",
    ),
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
    if (JSON.stringify([$("title").value, $("body").value]) === fingerprint) {
      $("capture-form").reset();
      remember("capture", null);
    }
    await refresh();
    captureDialog.close();
    showSource(source.id);
    note("Source saved. Create a draft when you are ready.");
  });
};
for (const id of ["title", "body"])
  $(id).oninput = () =>
    remember("capture", { title: $("title").value, body: $("body").value });
function applyLayout() {
  if (!state?.layout) return;
  for (const widget of [...state.layout.widgets].sort(
    (a, b) => a.order - b.order,
  )) {
    const element = $(widget.id);
    const target = $(widget.rail === "left" ? "capture-panel" : "review-panel");
    const order = state.layout.widgets
      .filter((w) => w.rail === widget.rail)
      .sort((a, b) => a.order - b.order)
      .findIndex((w) => w.id === widget.id);
    if (target.children[order] !== element)
      target.insertBefore(element, target.children[order] || null);
    element.hidden = !widget.visible;
    element.classList.toggle("collapsed", widget.collapsed);
    element.classList.toggle("compact", widget.density === "compact");
  }
  const list = state.layout.mode === "list";
  $("orbit").classList.toggle("list", list);
  $("view-mode").textContent = list ? "Map view" : "List view";
  $("view-mode").setAttribute("aria-pressed", String(list));
}
async function changeLayout(change) {
  await mutate(async () => {
    const desired = structuredClone(state.layout);
    change(desired);
    try {
      await api("/api/layout", { layout: desired });
    } finally {
      await refresh();
    }
  });
}
$("view-mode").onclick = () =>
  changeLayout((l) => (l.mode = l.mode === "map" ? "list" : "map"));
function arrange() {
  const body = open("Arrange your workspace", "PRESENTATION ONLY");
  body.append(
    el(
      "p",
      "Show, collapse, move or change the density of an instrument. Domain records are unaffected.",
    ),
  );
  for (const w of state.layout.widgets) {
    const row = el("div", undefined, "widget-controls");
    row.append(el("span", w.title));
    for (const [label, change] of [
      [
        w.visible ? "Hide" : "Show",
        (l) => (l.widgets.find((x) => x.id === w.id).visible = !w.visible),
      ],
      [
        w.collapsed ? "Expand" : "Collapse",
        (l) => (l.widgets.find((x) => x.id === w.id).collapsed = !w.collapsed),
      ],
      [
        w.density === "compact" ? "Comfortable" : "Compact",
        (l) =>
          (l.widgets.find((x) => x.id === w.id).density =
            w.density === "compact" ? "comfortable" : "compact"),
      ],
      [
        "Move rail",
        (l) => {
          const x = l.widgets.find((x) => x.id === w.id);
          x.rail = x.rail === "left" ? "right" : "left";
          x.order =
            Math.max(
              -1,
              ...l.widgets
                .filter((y) => y.id !== x.id && y.rail === x.rail)
                .map((y) => y.order),
            ) + 1;
        },
      ],
      [
        "Move earlier",
        (l) => {
          const x = l.widgets.find((x) => x.id === w.id);
          const previous = l.widgets
            .filter((y) => y.rail === x.rail && y.order < x.order)
            .sort((a, b) => b.order - a.order)[0];
          if (previous) [previous.order, x.order] = [x.order, previous.order];
        },
      ],
    ])
      row.append(
        button(
          label,
          async () => {
            await changeLayout(change);
            arrange();
          },
          "mutation",
        ),
      );
    body.append(row);
  }
  const actions = el("div", undefined, "actions");
  actions.append(
    button(
      "Restore layout",
      async () => {
        await changeLayout((l) => {
          for (const [i, w] of l.widgets.entries()) {
            w.visible = true;
            w.collapsed = false;
            w.density = "comfortable";
            w.rail = i < 2 ? "left" : "right";
            w.order = i % 2;
          }
          l.mode = "map";
        });
        close();
      },
      "mutation",
    ),
    button("New capture", () => {
      close();
      $("new-capture").onclick();
    }),
    button("Jobs", showJobs),
    button("Routines", showRoutines),
    button("Memory", showMemory),
    button("Provider setup", showProviders),
  );
  body.append(actions);
}
$("arrange").onclick = arrange;
$("guide-button").onclick = () => {
  const body = open("A small system that works", "ARMS WORKSPACE GUIDE");
  for (const [title, text] of [
    [
      "Applications",
      "This reference reads and writes its local records. No external account is connected.",
    ],
    [
      "Routines",
      "Create disabled interval routines, then enable explicitly. Automatic ticking requires starting the server with --routines.",
    ],
    [
      "Memory",
      "Captured sources, drafts, accepted projects and run events persist in SQLite.",
    ],
    [
      "Skills",
      "Capture-to-plan runs locally or through an explicitly configured provider. Every result remains a draft for review.",
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
    const saved = recalled("capture", null);
    if (
      saved &&
      typeof saved.title === "string" &&
      typeof saved.body === "string"
    ) {
      $("title").value = saved.title;
      $("body").value = saved.body;
    }
    setInterval(() => {
      if (
        !busy &&
        (state?.scheduler_active ||
          state?.jobs?.some((j) => ["queued", "running"].includes(j.status)))
      )
        refresh()
          .then(() => {
            if (currentRoute?.startsWith("job:"))
              showJob(currentRoute.slice(4), true);
          })
          .catch(() => {});
    }, 1000);
  } catch (e) {
    note(e.message);
  }
})();
function routeTo(route) {
  const [kind, id] = route.split(":");
  ({
    source: showSource,
    artifact: showArtifact,
    project: showProject,
    job: showJob,
  })[kind]?.(id);
}
$("inspector-back").onclick = () => {
  const previous = routeStack.pop();
  if (!previous) return;
  currentRoute = null;
  routeTo(previous.route);
  $("inspector-body").scrollTop = previous.scroll;
};
function editSource(id) {
  const s = state.sources.find((x) => x.id === id);
  const body = open("Edit source", "REVISION " + s.revision);
  const title = el("input");
  title.value = s.title;
  title.maxLength = 120;
  title.setAttribute("aria-label", "Source title");
  const text = el("textarea");
  text.value = s.body;
  text.maxLength = 12000;
  text.setAttribute("aria-label", "Source text");
  body.append(
    title,
    text,
    button(
      "Save source revision",
      () =>
        mutate(async () => {
          await api("/api/source/update", {
            source_id: id,
            revision: s.revision,
            title: title.value,
            body: text.value,
          });
          await refresh();
          showSource(id);
        }),
      "primary mutation",
    ),
  );
}
function showJobs() {
  const body = open("Jobs", "DURABLE WORK");
  if (!state.jobs.length)
    empty(body, "Select a source and Run skill to create a durable job.");
  state.jobs.forEach((j) =>
    record(body, j.provider_id + " · " + j.status, date(j.created_at), () =>
      showJob(j.id),
    ),
  );
}
function showJob(id, quiet = false) {
  const job = state.jobs.find((x) => x.id === id);
  if (!job) return;
  const focused = document.activeElement;
  const scroll = $("inspector-body").scrollTop;
  const body = open(
    "Capture to plan",
    "JOB · " + job.status.toUpperCase(),
    "job:" + id,
  );
  body.append(
    el("p", "Provider: " + job.provider_id + " · attempt " + job.attempts),
    el("p", "Created " + date(job.created_at)),
    el("p", "Source digest: " + job.source_digest, "footnote"),
  );
  if (job.error) body.append(el("p", job.error, "error"));
  const actions = el("div", undefined, "actions");
  actions.append(button("Inspect source", () => showSource(job.source_id)));
  if (["queued", "running"].includes(job.status)) {
    actions.append(
      el(
        "p",
        job.cancel_requested
          ? "Stop requested; waiting for worker confirmation."
          : "The worker records the result before reporting completion.",
      ),
    );
    if (!job.cancel_requested)
      actions.append(
        button(
          "Stop job",
          () =>
            mutate(async () => {
              await api("/api/jobs/cancel", { job_id: id });
              await refresh();
              showJob(id);
            }),
          "mutation",
        ),
      );
  }
  if (job.artifact_id)
    actions.append(
      button("Open job result", () => showArtifact(job.artifact_id), "primary"),
    );
  body.append(actions);
  if (quiet) {
    $("inspector-body").scrollTop = scroll;
    if (focused?.id && $(focused.id)) $(focused.id).focus();
  }
}
function createRoutine(sourceId, providerId) {
  const body = open("Schedule a source review", "CREATED PAUSED");
  body.append(
    el(
      "p",
      "Elapsed-time interval in UTC. Missed intervals coalesce to the latest occurrence. The scheduler must be explicitly started.",
    ),
  );
  const interval = el("input");
  interval.type = "number";
  interval.min = "60";
  interval.value = "86400";
  interval.setAttribute("aria-label", "Interval seconds");
  const due = el("input");
  due.value = new Date(Date.now() + 86400000).toISOString();
  due.setAttribute("aria-label", "First run UTC");
  body.append(
    el("label", "Interval seconds"),
    interval,
    el("label", "First run ISO timestamp"),
    due,
    button(
      "Create paused routine",
      () =>
        mutate(async () => {
          await api("/api/routines", {
            source_id: sourceId,
            provider_id: providerId,
            interval_seconds: Number(interval.value),
            next_due_at: due.value,
          });
          await refresh();
          showRoutines();
        }),
      "primary mutation",
    ),
  );
}
function showRoutines() {
  const body = open("Routines", "LOCAL SCHEDULER");
  body.append(
    el(
      "p",
      state.scheduler_active
        ? "This server ticks explicitly enabled routines."
        : "Scheduler is off. Start with --routines or use the CLI tick command.",
    ),
  );
  if (!state.routines.length)
    empty(body, "Open a source to create a paused routine.");
  for (const r of state.routines) {
    const row = el("section", undefined, "routine-row");
    row.append(
      el(
        "h3",
        state.sources.find((s) => s.id === r.source_id)?.title ||
          "Missing source",
      ),
      el(
        "p",
        (r.enabled ? "Enabled" : "Paused") +
          " · every " +
          r.interval_seconds +
          " seconds · next " +
          date(r.next_due_at),
      ),
    );
    if (r.last_error) row.append(el("p", r.last_error));
    row.append(
      button(
        r.enabled ? "Pause routine" : "Enable routine",
        () =>
          mutate(async () => {
            await api("/api/routines/enable", {
              routine_id: r.id,
              revision: r.revision,
              enabled: !r.enabled,
            });
            await refresh();
            showRoutines();
          }),
        "mutation",
      ),
    );
    body.append(row);
  }
}
$("routine-control").onclick = showRoutines;
async function showMemory() {
  const body = open("Memory", "SOURCE-AWARE RETRIEVAL");
  const input = el("input");
  input.type = "search";
  input.placeholder = "Search evidence and accepted decisions";
  input.setAttribute("aria-label", "Search memory");
  const results = el("div");
  body.append(input, results);
  let generation = 0;
  const search = async () => {
    const version = ++generation;
    try {
      const rows = await api(
        "/api/memory?q=" + encodeURIComponent(input.value),
      );
      if (version !== generation || !results.isConnected) return;
      results.replaceChildren();
      if (!rows.length) empty(results, "No matching evidence.");
      rows.forEach((r) =>
        record(results, r.title, r.kind + " · " + r.status, () =>
          r.kind === "source" ? showSource(r.id) : showArtifact(r.id),
        ),
      );
    } catch (e) {
      note(e.message);
    }
  };
  input.oninput = search;
  await search();
}
async function showProviders() {
  const body = open("Provider setup", "STATIC DIAGNOSTICS");
  try {
    const d = await api("/api/doctor");
    body.append(el("p", d.note));
    for (const p of d.instances)
      body.append(el("h3", p.id), el("p", p.transport + " · " + p.status));
    if (d.configuration_error) body.append(el("p", d.configuration_error));
    body.append(
      el(
        "p",
        "Use docs/quickstart.md to configure a user-owned ACP session or API endpoint. No login or provider calls occur from this screen.",
      ),
    );
  } catch (e) {
    note(e.message);
  }
}
function renderDomain() {
  document.title = "AgentOS · " + state.profile.name;
  document.querySelector(".center-object .eyebrow").textContent =
    state.profile.name;
  document.body.dataset.composition = "orbital";
  document.body.dataset.profile = state.profile.profile;
  $("domain-surface").hidden = true;
  $("orbit").hidden = false;
  $("view-mode").hidden = false;
  const names = {
    research: ["Evidence", "Briefs", "Research", "Runs"],
    operations: ["Intake", "Plans", "Projects", "Runs"],
    monitoring: ["Observations", "Reviews", "Investigations", "Runs"],
  }[state.profile.profile] || ["Sources", "Drafts", "Projects", "Runs"];
  ["sources", "drafts", "projects", "runs"].forEach(
    (name, i) =>
      (document.querySelector("." + name + "-node strong").textContent =
        names[i]),
  );
}
function showDomainView() {
  const composition = state.profile.detail_view;
  const surface = open(
    state.profile.name,
    composition === "workbench"
      ? "EVIDENCE WORKBENCH"
      : composition === "board"
        ? "OPERATIONS BOARD"
        : "DOMAIN RECORDS",
  );
  if (composition === "workbench") {
    const latest = state.artifacts[0];
    if (latest) {
      surface.append(
        el("h3", latest.content.title),
        el("p", latest.content.objective),
        el("p", "Draft · " + latest.review, "muted"),
        button("Inspect working draft", () => showArtifact(latest.id)),
      );
    } else empty(surface, "Capture a source to begin a research brief.");
    const shelf = el("div", undefined, "source-shelf");
    state.sources
      .slice(0, 8)
      .forEach((s) =>
        record(shelf, s.title, "Evidence · " + date(s.observed_at), () =>
          showSource(s.id),
        ),
      );
    surface.append(shelf);
  } else {
    const lanes = el("div", undefined, "work-lanes");
    for (const [title, rows, show] of [
      ["Intake", state.sources, showSource],
      [
        "Drafts",
        state.artifacts.filter((a) => a.review === "pending"),
        showArtifact,
      ],
      ["Accepted", state.projects, showProject],
    ]) {
      const lane = el("section");
      lane.append(el("h3", title));
      if (!rows.length) empty(lane, "No " + title.toLowerCase() + " yet.");
      rows
        .slice(0, 8)
        .forEach((r) =>
          record(lane, r.title || r.content.title, "Inspect →", () =>
            show(r.id),
          ),
        );
      lanes.append(lane);
    }
    surface.append(lanes);
  }
}
async function showSkills() {
  const body = open("Project skills", "BUILDER PLAYBOOKS");
  try {
    const skills = await api("/api/skills");
    body.append(
      el(
        "p",
        "Project-scoped instructions. Reading a playbook does not launch it or grant tools.",
      ),
    );
    skills.forEach((s) =>
      record(body, s.name, s.description, async () => {
        const content = await api(
          "/api/skills?id=" + encodeURIComponent(s.name),
        );
        const view = open(s.name, "PROJECT PLAYBOOK");
        view.append(el("pre", content.text));
      }),
    );
  } catch (e) {
    note(e.message);
  }
}
function showApps() {
  const body = open("Workspace apps", "CONTEXTUAL VIEWS");
  const actions = el("div", undefined, "actions");
  actions.append(
    button("Work view", showDomainView),
    button("Jobs", showJobs),
    button("Routines", showRoutines),
    button("Memory", showMemory),
    button("Skills", showSkills),
    button("Provider setup", showProviders),
    button("All instruments", arrange),
  );
  body.append(actions);
}
$("workspace-center").onclick = showApps;
$("apps-orbit").onclick = showApps;
$("skills-orbit").onclick = showSkills;
$("memory-orbit").onclick = showMemory;
$("routines-orbit").onclick = showRoutines;
