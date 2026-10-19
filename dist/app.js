"use strict";

const arrowOrder = ["R", "D", "L", "U"];
const arrowGlyph = { R: "→", D: "↓", L: "←", U: "↑" };
const arrowName = { R: "Right", D: "Down", L: "Left", U: "Up" };
const delta = { R: [0, 1], D: [1, 0], L: [0, -1], U: [-1, 0] };

const gridElement = document.querySelector("#direction-grid");
const gridStatus = document.querySelector("#grid-status");
const gridCurrent = document.querySelector("#grid-current");
const gridVisited = document.querySelector("#grid-visited");
const gridNext = document.querySelector("#grid-next");
const gridProgress = document.querySelector("#grid-progress");
const gridStepButton = document.querySelector("#grid-step");
const gridPlayButton = document.querySelector("#grid-play");
const gridResetButton = document.querySelector("#grid-reset");

let grid = [["R", "D"], ["U", "L"]];
let gridState;
let gridTimer = null;

function gridKey(row, col) {
  return `${row},${col}`;
}

function resetGridState() {
  stopGridPlayback();
  gridState = { row: 0, col: 0, visited: new Set(), stopped: false, reason: "" };
  renderGrid();
}

function renderGrid() {
  gridElement.replaceChildren();
  grid.forEach((rowValues, row) => {
    rowValues.forEach((direction, col) => {
      const cell = document.createElement("button");
      const key = gridKey(row, col);
      cell.type = "button";
      cell.className = "direction-cell";
      cell.setAttribute("role", "gridcell");
      cell.setAttribute("aria-label", `Cell ${row}, ${col}, points ${arrowName[direction]}. Click to rotate.`);
      cell.innerHTML = `<small>(${row}, ${col})</small><span aria-hidden="true">${arrowGlyph[direction]}</span>`;
      if (gridState.visited.has(key)) cell.classList.add("visited");
      if (!gridState.stopped && row === gridState.row && col === gridState.col) cell.classList.add("current");
      if (gridState.stopped && row === gridState.row && col === gridState.col) cell.classList.add("blocked");
      cell.addEventListener("click", () => rotateCell(row, col));
      gridElement.append(cell);
    });
  });

  const currentDirection = grid[gridState.row][gridState.col];
  gridCurrent.textContent = `(${gridState.row}, ${gridState.col})`;
  gridVisited.textContent = `${gridState.visited.size} / ${grid.length * grid[0].length}`;
  gridNext.textContent = arrowName[currentDirection];
  gridProgress.style.width = `${(gridState.visited.size / (grid.length * grid[0].length)) * 100}%`;
  gridStatus.textContent = gridState.stopped
    ? `${gridState.reason} Answer: (${gridState.row}, ${gridState.col}).`
    : gridState.visited.size
      ? `Standing at (${gridState.row}, ${gridState.col})`
      : "Ready at (0, 0)";
  gridStepButton.disabled = gridState.stopped;
}

function rotateCell(row, col) {
  const oldDirection = grid[row][col];
  grid[row][col] = arrowOrder[(arrowOrder.indexOf(oldDirection) + 1) % arrowOrder.length];
  resetGridState();
}

function stepGrid() {
  if (gridState.stopped) return false;

  const { row, col } = gridState;
  gridState.visited.add(gridKey(row, col));
  const [dr, dc] = delta[grid[row][col]];
  const nextRow = row + dr;
  const nextCol = col + dc;
  const outside = nextRow < 0 || nextRow >= grid.length || nextCol < 0 || nextCol >= grid[0].length;
  const repeated = !outside && gridState.visited.has(gridKey(nextRow, nextCol));

  if (outside || repeated) {
    gridState.stopped = true;
    gridState.reason = outside ? "The next move leaves the grid." : `(${nextRow}, ${nextCol}) was already visited.`;
    stopGridPlayback();
  } else {
    gridState.row = nextRow;
    gridState.col = nextCol;
  }
  renderGrid();
  return !gridState.stopped;
}

function stopGridPlayback() {
  if (gridTimer) window.clearInterval(gridTimer);
  gridTimer = null;
  if (gridPlayButton) gridPlayButton.textContent = "Auto play";
}

function toggleGridPlayback() {
  if (gridTimer) {
    stopGridPlayback();
    return;
  }
  if (gridState.stopped) resetGridState();
  gridPlayButton.textContent = "Pause";
  gridTimer = window.setInterval(() => {
    if (!stepGrid()) stopGridPlayback();
  }, 650);
}

gridStepButton.addEventListener("click", stepGrid);
gridPlayButton.addEventListener("click", toggleGridPlayback);
gridResetButton.addEventListener("click", resetGridState);
resetGridState();

const treePresets = {
  valid: {
    nodes: [
      { id: 0, color: "R", x: 310, y: 55 },
      { id: 1, color: "B", x: 180, y: 175 },
      { id: 2, color: "B", x: 445, y: 175 },
      { id: 3, color: "W", x: 100, y: 305 },
      { id: 4, color: "W", x: 255, y: 305 },
    ],
    edges: [[0, 1], [0, 2], [1, 3], [1, 4]],
  },
  multiple: {
    nodes: [
      { id: 0, color: "R", x: 95, y: 180 },
      { id: 1, color: "B", x: 310, y: 180 },
      { id: 2, color: "R", x: 525, y: 180 },
    ],
    edges: [[0, 1], [1, 2]],
  },
  degree: {
    nodes: [
      { id: 0, color: "R", x: 310, y: 165 },
      { id: 1, color: "B", x: 115, y: 65 },
      { id: 2, color: "B", x: 505, y: 65 },
      { id: 3, color: "B", x: 310, y: 310 },
    ],
    edges: [[0, 1], [0, 2], [0, 3]],
  },
};

const nextColor = { R: "B", B: "W", W: "R" };
const colorFill = { R: "#ef4a3a", B: "#2d6cdf", W: "#ffffff" };
const colorText = { R: "#ffffff", B: "#ffffff", W: "#171717" };
const treeCanvas = document.querySelector("#tree-canvas");
const treeStatus = document.querySelector("#tree-status");
const indegreeList = document.querySelector("#indegree-list");
const treeResult = document.querySelector("#tree-result");
const treeStepButton = document.querySelector("#tree-step");
const treePlayButton = document.querySelector("#tree-play");
const treeResetButton = document.querySelector("#tree-reset");
const presetButtons = [...document.querySelectorAll("[data-tree-preset]")];

let activePreset = "valid";
let treeState;
let treeTimer = null;

function svgElement(name, attributes = {}) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function resetTreeState() {
  stopTreePlayback();
  const preset = treePresets[activePreset];
  treeState = {
    edgeIndex: 0,
    indegree: Array(preset.nodes.length).fill(0),
    degree: Array(preset.nodes.length).fill(0),
    oriented: [],
    impossible: false,
    complete: false,
  };
  preset.edges.forEach(([u, v]) => { treeState.degree[u] += 1; treeState.degree[v] += 1; });
  renderTree();
}

function shortenedLine(from, to, radius = 37) {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const length = Math.hypot(dx, dy);
  const ux = dx / length;
  const uy = dy / length;
  return {
    x1: from.x + ux * radius,
    y1: from.y + uy * radius,
    x2: to.x - ux * (radius + 8),
    y2: to.y - uy * (radius + 8),
  };
}

function renderTree() {
  const preset = treePresets[activePreset];
  treeCanvas.replaceChildren();

  const defs = svgElement("defs");
  const marker = svgElement("marker", { id: "tree-arrow", markerWidth: 10, markerHeight: 10, refX: 8, refY: 3, orient: "auto" });
  marker.append(svgElement("path", { d: "M0,0 L0,6 L9,3 z", fill: "#171717" }));
  defs.append(marker);
  treeCanvas.append(defs);

  preset.edges.forEach(([originalU, originalV], index) => {
    const orientation = treeState.oriented[index];
    const fromId = orientation ? orientation[0] : originalU;
    const toId = orientation ? orientation[1] : originalV;
    const from = preset.nodes[fromId];
    const to = preset.nodes[toId];
    const points = shortenedLine(from, to);
    const line = svgElement("line", { ...points, class: `tree-edge${orientation ? " oriented" : ""}${index === treeState.edgeIndex && !treeState.complete ? " active" : ""}` });
    treeCanvas.append(line);
  });

  const verdict = treeState.complete ? evaluateTree() : null;
  preset.nodes.forEach((node) => {
    const group = svgElement("g", { class: "tree-node" });
    if (verdict?.root === node.id && verdict.valid) group.classList.add("root");
    if (verdict?.invalidNodes.includes(node.id)) group.classList.add("invalid");
    const circle = svgElement("circle", { cx: node.x, cy: node.y, r: 37, fill: colorFill[node.color] });
    const color = svgElement("text", { x: node.x, y: node.y - 3, fill: colorText[node.color], "font-size": 22 });
    color.textContent = node.color;
    const label = svgElement("text", { x: node.x, y: node.y + 57, class: "tree-label" });
    label.textContent = `node ${node.id} · in ${treeState.indegree[node.id]}`;
    group.append(circle, color, label);
    treeCanvas.append(group);
  });

  indegreeList.replaceChildren();
  treeState.indegree.forEach((incoming, node) => {
    const chip = document.createElement("span");
    chip.className = `indegree-chip${incoming === 0 ? " zero" : ""}${incoming > 1 ? " over" : ""}`;
    chip.textContent = `${node}: in ${incoming}`;
    indegreeList.append(chip);
  });

  if (treeState.complete) {
    showTreeVerdict(verdict);
  } else {
    treeStatus.textContent = treeState.edgeIndex
      ? `${treeState.edgeIndex} of ${preset.edges.length} edges oriented`
      : "Ready to inspect edges";
    treeResult.className = "result-banner";
    treeResult.textContent = "Process every edge to reveal the root.";
  }
  treeStepButton.disabled = treeState.complete;
}

function stepTree() {
  const preset = treePresets[activePreset];
  if (treeState.complete) return false;
  const [u, v] = preset.edges[treeState.edgeIndex];
  const uColor = preset.nodes[u].color;
  const vColor = preset.nodes[v].color;

  let orientation;
  if (nextColor[uColor] === vColor) orientation = [u, v];
  else if (nextColor[vColor] === uColor) orientation = [v, u];
  else {
    orientation = [u, v];
    treeState.impossible = true;
  }

  treeState.oriented.push(orientation);
  treeState.indegree[orientation[1]] += 1;
  treeState.edgeIndex += 1;
  treeState.complete = treeState.impossible || treeState.edgeIndex === preset.edges.length;
  if (treeState.complete) stopTreePlayback();
  renderTree();
  return !treeState.complete;
}

function evaluateTree() {
  const roots = treeState.indegree.map((value, index) => value === 0 ? index : -1).filter((index) => index >= 0);
  const invalidNodes = treeState.indegree.map((value, index) => value > 1 ? index : -1).filter((index) => index >= 0);
  const root = roots.length === 1 ? roots[0] : -1;
  if (root >= 0 && treeState.degree[root] > 2) invalidNodes.push(root);
  const valid = !treeState.impossible && roots.length === 1 && invalidNodes.length === 0 &&
    treeState.indegree.every((incoming, node) => node === root || incoming === 1);
  return { valid, root, roots, invalidNodes };
}

function showTreeVerdict(verdict) {
  if (verdict.valid) {
    treeStatus.textContent = `Node ${verdict.root} is the unique indegree-zero node.`;
    treeResult.className = "result-banner success";
    treeResult.textContent = `Root found: node ${verdict.root}. Its degree is ${treeState.degree[verdict.root]}, so the tree is binary.`;
  } else if (verdict.roots.length > 1) {
    treeStatus.textContent = `${verdict.roots.length} nodes have no incoming edge.`;
    treeResult.className = "result-banner failure";
    treeResult.textContent = `Invalid: candidates ${verdict.roots.join(", ")} cannot both be the root; another node receives two parents.`;
  } else if (verdict.root >= 0 && treeState.degree[verdict.root] > 2) {
    treeStatus.textContent = `Node ${verdict.root} has indegree 0—but degree ${treeState.degree[verdict.root]}.`;
    treeResult.className = "result-banner failure";
    treeResult.textContent = "Invalid: the root would have three children, violating the binary-tree rule.";
  } else {
    treeStatus.textContent = "The oriented edges do not form one rooted tree.";
    treeResult.className = "result-banner failure";
    treeResult.textContent = "Invalid: every non-root needs exactly one incoming parent edge.";
  }
}

function stopTreePlayback() {
  if (treeTimer) window.clearInterval(treeTimer);
  treeTimer = null;
  if (treePlayButton) treePlayButton.textContent = "Auto play";
}

function toggleTreePlayback() {
  if (treeTimer) {
    stopTreePlayback();
    return;
  }
  if (treeState.complete) resetTreeState();
  treePlayButton.textContent = "Pause";
  treeTimer = window.setInterval(() => {
    if (!stepTree()) stopTreePlayback();
  }, 780);
}

presetButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activePreset = button.dataset.treePreset;
    presetButtons.forEach((item) => item.classList.toggle("active", item === button));
    resetTreeState();
  });
});
treeStepButton.addEventListener("click", stepTree);
treePlayButton.addEventListener("click", toggleTreePlayback);
treeResetButton.addEventListener("click", resetTreeState);
resetTreeState();

document.querySelector("#year").textContent = new Date().getFullYear();

const catalog = window.KATALCODE_CATALOG;
const views = [...document.querySelectorAll("[data-view]")];
const platformGrid = document.querySelector("#platform-grid");
const contestList = document.querySelector("#contest-list");
const questionList = document.querySelector("#question-list");
const searchInput = document.querySelector("#contest-search");
const chapterTabs = [...document.querySelectorAll("[data-chapter]")];
const chapterPanels = [...document.querySelectorAll("[data-chapter-panel]")];
let activePlatform = "leetcode";

function element(tag, className, content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = content;
  return node;
}

function link(className, label, href) {
  const node = element("a", className, label);
  node.href = href;
  return node;
}

function platformHref(platformId) {
  return `#platform/${platformId}`;
}

function contestHref(platformId, contestId) {
  return `#contest/${platformId}/${contestId}`;
}

function problemHref(platformId, contestId, problemId) {
  return `#problem/${platformId}/${contestId}/${problemId}`;
}

function showView(name) {
  views.forEach((view) => { view.hidden = view.dataset.view !== name; });
}

function renderPlatforms() {
  platformGrid.replaceChildren();
  Object.entries(catalog).forEach(([id, platform]) => {
    const card = link(`platform-card platform-${id}`, "", platformHref(id));
    const count = platform.contests.length;
    const head = element("div", "platform-card-head");
    head.append(element("span", "platform-monogram", platform.initials), element("span", "platform-count", `${count} ${count === 1 ? "contest" : "contests"}`));
    card.append(head, element("h3", "", platform.name), element("p", "", platform.description), element("span", "platform-cta", "Browse contests →"));
    platformGrid.append(card);
  });
}

function renderContestList() {
  const platform = catalog[activePlatform];
  const search = searchInput.value.trim().toLowerCase();
  const contests = platform.contests.filter((contest) => `${contest.title} ${contest.type} ${contest.date}`.toLowerCase().includes(search));
  contestList.replaceChildren();
  if (platform.contests.length === 0) {
    const empty = element("div", "empty-state");
    empty.append(element("h2", "", "No contests documented yet"), element("p", "", `${platform.name} editorials will appear here when they are added to the archive.`), link("button button-primary", `Browse ${platform.name} contests ↗`, platform.archiveUrl), link("button button-ghost", "Choose another platform", "#home"));
    contestList.append(empty);
    return;
  }
  if (contests.length === 0) {
    contestList.append(element("p", "empty-search", "No contests match your search."));
    return;
  }
  contests.forEach((contest) => {
    const row = link("contest-row", "", contestHref(activePlatform, contest.id));
    const main = element("div", "contest-row-main");
    main.append(element("span", "row-eyebrow", `${contest.type} · ${contest.date}`), element("h2", "", contest.title), element("p", "", contest.summary));
    row.append(main, element("span", "row-count", `${contest.problems.length} ${contest.problems.length === 1 ? "question" : "questions"}`), element("span", "row-arrow", "→"));
    contestList.append(row);
  });
}

function renderPlatform(platformId) {
  activePlatform = platformId;
  const platform = catalog[platformId];
  document.querySelector("#platform-badge").textContent = platform.initials;
  document.querySelector("#platform-name").textContent = platform.name;
  document.querySelector("#platform-description").textContent = platform.description;
  document.querySelector("#platform-kicker").textContent = "PLATFORM ARCHIVE";
  document.querySelector("#contest-count").textContent = `${platform.contests.length} ${platform.contests.length === 1 ? "contest" : "contests"}`;
  const questions = platform.contests.reduce((count, contest) => count + contest.problems.length, 0);
  document.querySelector("#problem-count").textContent = `${questions} ${questions === 1 ? "question" : "questions"}`;
  searchInput.value = "";
  searchInput.closest("label").hidden = platform.contests.length === 0;
  renderContestList();
  showView("platform");
  document.title = `${platform.name} contests · KatalCode`;
}

function renderContest(platformId, contest) {
  const platform = catalog[platformId];
  document.querySelector("#contest-back").href = platformHref(platformId);
  document.querySelector("#contest-kicker").textContent = `${platform.name.toUpperCase()} · ${contest.type.toUpperCase()}`;
  document.querySelector("#contest-title").textContent = contest.title;
  document.querySelector("#contest-summary").textContent = contest.summary;
  document.querySelector("#contest-meta").textContent = `${contest.date} · ${contest.problems.length} documented questions`;
  questionList.replaceChildren();
  contest.problems.forEach((problem) => {
    const row = link("question-row", "", problemHref(platformId, contest.id, problem.id));
    row.append(element("span", "question-number", problem.number));
    const main = element("div", "question-row-main");
    main.append(element("span", "row-eyebrow", `${problem.platformId} · ${problem.pattern}`), element("h2", "", problem.title), element("p", "", problem.summary));
    row.append(main, element("span", "difficulty", problem.difficulty), element("span", "row-arrow", "→"));
    questionList.append(row);
  });
  showView("contest");
  document.title = `${contest.title} · KatalCode`;
}

function selectChapter(chapter) {
  chapterTabs.forEach((tab) => {
    const selected = tab.dataset.chapter === chapter;
    tab.classList.toggle("active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });
  chapterPanels.forEach((panel) => { panel.hidden = panel.dataset.chapterPanel !== chapter; });
}

function renderProblem(platformId, contest, problem) {
  const platform = catalog[platformId];
  document.querySelector("#problem-back").href = contestHref(platformId, contest.id);
  document.querySelector("#problem-kicker").textContent = `${platform.name.toUpperCase()} ${problem.platformId} · ${contest.title.toUpperCase()} · ${problem.number}`;
  document.querySelector("#problem-title").textContent = problem.title;
  document.querySelector("#problem-summary").textContent = problem.summary;
  document.querySelector("#problem-difficulty").textContent = problem.difficulty;
  document.querySelector("#source-editorial").href = `https://github.com/KatalKavya96/KatalCode/blob/main/${problem.source}`;
  document.querySelector("#learn-title").textContent = problem.storyTitle;
  document.querySelector("#learn-intro").textContent = problem.intro;
  document.querySelector("#key-insight").textContent = problem.insight;
  const sequence = document.querySelector("#comic-sequence");
  sequence.replaceChildren();
  problem.panels.forEach(([label, heading, body], index) => {
    const panel = element("article", `comic-panel${index === 1 ? " accent-panel" : ""}${index === 2 ? " dark-panel" : ""}`);
    panel.append(element("span", "panel-index", String(index + 1)), element("p", "narration", label), element("h3", "", heading), element("p", "", body));
    sequence.append(panel);
  });
  const takeaways = document.querySelector("#takeaway-grid");
  takeaways.replaceChildren();
  problem.takeaways.forEach((takeaway, index) => {
    const card = element("article", "takeaway-card");
    card.append(element("span", "", String(index + 1).padStart(2, "0")), element("p", "", takeaway));
    takeaways.append(card);
  });
  document.querySelector("#grid-simulator").hidden = problem.simulator !== "grid";
  document.querySelector("#tree-simulator").hidden = problem.simulator !== "tree";
  stopGridPlayback();
  stopTreePlayback();
  selectChapter("learn");
  showView("problem");
  document.title = `${problem.title} · KatalCode`;
}

function navigate() {
  const hash = decodeURIComponent(window.location.hash.slice(1));
  const parts = hash.split("/");
  const [page, platformId, contestId, problemId] = parts;
  const platform = catalog[platformId];
  const contest = platform?.contests.find((item) => item.id === contestId);
  const problem = contest?.problems.find((item) => item.id === problemId);

  if (page === "platform" && platform && parts.length === 2) renderPlatform(platformId);
  else if (page === "contest" && contest && parts.length === 3) renderContest(platformId, contest);
  else if (page === "problem" && problem && parts.length === 4) renderProblem(platformId, contest, problem);
  else {
    showView("home");
    document.title = "KatalCode — Visual Algorithm Archive";
  }

  if (hash === "platforms") document.querySelector("#platforms").scrollIntoView();
  else window.scrollTo(0, 0);
}

renderPlatforms();
document.querySelector(".skip-link").addEventListener("click", (event) => {
  event.preventDefault();
  document.querySelector("#content").focus();
});
searchInput.addEventListener("input", renderContestList);
chapterTabs.forEach((tab) => tab.addEventListener("click", () => selectChapter(tab.dataset.chapter)));
window.addEventListener("hashchange", navigate);
navigate();
