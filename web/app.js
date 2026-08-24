const form = document.querySelector("#research-form");
const areaInput = document.querySelector("#area");
const statusBox = document.querySelector("#status");
const report = document.querySelector("#report");
const submitButton = form.querySelector("button");
const accessKeyInput = document.querySelector("#access-key");

const progressMessages = [
  "Map Scout is checking qualified places…",
  "Review Analyst is finding useful signals…",
  "Briefing Editor is trimming the report…",
];

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const area = areaInput.value.trim();
  if (!area) return;

  setLoading(true);
  let messageIndex = 0;
  statusBox.textContent = progressMessages[messageIndex];
  const progressTimer = setInterval(() => {
    messageIndex = Math.min(messageIndex + 1, progressMessages.length - 1);
    statusBox.textContent = progressMessages[messageIndex];
  }, 4500);

  try {
    const headers = { "Content-Type": "application/json" };
    if (accessKeyInput.value) headers["X-App-Key"] = accessKeyInput.value;

    const response = await fetch("/api/research", {
      method: "POST",
      headers,
      body: JSON.stringify({ area }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Research failed.");
    renderReport(data);
  } catch (error) {
    showError(error.message);
  } finally {
    clearInterval(progressTimer);
    submitButton.disabled = false;
    submitButton.textContent = "Scout";
  }
});

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Scouting…" : "Scout";
  report.hidden = true;
  statusBox.hidden = !isLoading;
  statusBox.classList.remove("error");
}

function showError(message) {
  statusBox.hidden = false;
  statusBox.classList.add("error");
  statusBox.textContent = message;
}

function renderReport(data) {
  statusBox.hidden = true;
  report.hidden = false;
  document.querySelector("#report-kicker").textContent = "Your shortlist";
  document.querySelector("#report-title").textContent = data.area;
  document.querySelector("#area-style").textContent = `${data.area_style} leaning`;
  document.querySelector("#area-summary").textContent = data.area_summary;
  document.querySelector("#report-counts").textContent =
    `Checked ${data.scanned_count} map results · ${data.qualified_count} met the filters · showing ${data.shown_count}`;
  document.querySelector("#review-note").textContent = data.review_note;

  const places = document.querySelector("#places");
  places.replaceChildren(...data.places.map(placeCard));
  report.scrollIntoView({ behavior: "smooth", block: "start" });
}

function placeCard(place) {
  const card = element("article", "place-card");
  const top = element("div", "place-top");
  const heading = element("div");
  heading.append(
    textElement("h3", place.name),
    textElement("p", place.address, "address"),
  );
  const rating = element("div", "rating");
  rating.append(document.createTextNode(`★ ${place.rating.toFixed(1)} `));
  rating.append(textElement("span", `(${formatCount(place.review_count)})`));
  top.append(heading, rating);

  const tags = element("div", "tags");
  tags.append(
    textElement("span", place.style, "place-style"),
    textElement("span", place.best_for, "best-for"),
  );
  if (place.primary_type) tags.append(textElement("span", place.primary_type, "place-style"));

  card.append(
    top,
    tags,
    textElement("p", place.why_it_stands_out, "standout"),
    textElement("p", `Review signal: ${place.review_summary}`, "signal"),
  );
  if (place.watch_out) card.append(textElement("p", `Worth knowing: ${place.watch_out}`, "watch-out"));

  const actions = element("div", "actions");
  actions.append(link("Open in Google Maps ↗", place.google_maps_url));
  if (place.website_url) actions.append(link("Website ↗", place.website_url));
  card.append(actions);
  return card;
}

function element(tag, className = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  return node;
}

function textElement(tag, text, className = "") {
  const node = element(tag, className);
  node.textContent = text;
  return node;
}

function link(label, url) {
  const node = textElement("a", label);
  node.href = url;
  node.target = "_blank";
  node.rel = "noopener noreferrer";
  return node;
}

function formatCount(value) {
  return new Intl.NumberFormat(undefined, { notation: "compact" }).format(value);
}
