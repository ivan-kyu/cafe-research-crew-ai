const form = document.querySelector("#research-form");
const areaInput = document.querySelector("#area");
const statusBox = document.querySelector("#status");
const report = document.querySelector("#report");
const submitButton = form.querySelector("button");
const accessKeyInput = document.querySelector("#access-key");
const activePhotoUrls = new Set();
const PHOTO_BATCH_SIZE = 3;

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
  revokePhotoUrls();
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

  if (place.photos?.length) card.append(photoGallery(place));

  const actions = element("div", "actions");
  actions.append(link("Open in Google Maps ↗", place.google_maps_url));
  if (place.website_url) actions.append(link("Website ↗", place.website_url));
  card.append(actions);
  return card;
}

function photoGallery(place) {
  const section = element("section", "photo-section");
  const heading = element("div", "photo-heading");
  heading.append(
    textElement("h4", "Place photos"),
    textElement("span", "Google relevance order"),
  );

  const gallery = element("div", "photo-gallery");
  let shown = 0;

  const showNextBatch = () => {
    const nextPhotos = place.photos.slice(shown, shown + PHOTO_BATCH_SIZE);
    gallery.append(...nextPhotos.map((photo, offset) => photoTile(place, photo, shown + offset)));
    shown += nextPhotos.length;
    moreButton.hidden = shown >= place.photos.length;
    moreButton.textContent = `Load more photos (${place.photos.length - shown})`;
  };

  const moreButton = textElement("button", "", "photo-more");
  moreButton.type = "button";
  moreButton.addEventListener("click", showNextBatch);
  section.append(heading, gallery, moreButton);
  showNextBatch();
  return section;
}

function photoTile(place, photo, index) {
  const figure = element("figure", "photo-tile is-loading");
  const image = document.createElement("img");
  image.alt = `${place.name}, place photo ${index + 1}`;
  image.loading = "lazy";
  image.decoding = "async";

  const media = photo.google_maps_url ? link("", normalizeUrl(photo.google_maps_url)) : element("div");
  media.className = "photo-media";
  media.append(image);
  figure.append(media);

  const authors = (photo.author_attributions || []).filter((author) => author.display_name);
  if (authors.length) {
    const caption = textElement("figcaption", "Photo by ");
    authors.forEach((author, authorIndex) => {
      if (authorIndex) caption.append(document.createTextNode(", "));
      caption.append(
        author.uri
          ? link(author.display_name, normalizeUrl(author.uri))
          : document.createTextNode(author.display_name),
      );
    });
    figure.append(caption);
  }

  observePhoto(image, photo.name, figure);
  return figure;
}

function observePhoto(image, photoName, figure) {
  if (!("IntersectionObserver" in window)) {
    loadPhoto(image, photoName, figure);
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    if (!entries.some((entry) => entry.isIntersecting)) return;
    observer.disconnect();
    loadPhoto(image, photoName, figure);
  }, { rootMargin: "240px" });
  observer.observe(image);
}

async function loadPhoto(image, photoName, figure) {
  try {
    const headers = {};
    if (accessKeyInput.value) headers["X-App-Key"] = accessKeyInput.value;
    const response = await fetch(`/api/place-photo?name=${encodeURIComponent(photoName)}`, { headers });
    if (!response.ok) throw new Error("Photo unavailable");
    const objectUrl = URL.createObjectURL(await response.blob());
    activePhotoUrls.add(objectUrl);
    image.src = objectUrl;
    image.addEventListener("load", () => figure.classList.remove("is-loading"), { once: true });
  } catch {
    figure.classList.remove("is-loading");
    figure.classList.add("is-error");
    image.alt = "Photo unavailable";
  }
}

function revokePhotoUrls() {
  activePhotoUrls.forEach((url) => URL.revokeObjectURL(url));
  activePhotoUrls.clear();
}

function normalizeUrl(url) {
  return url.startsWith("//") ? `https:${url}` : url;
}

window.addEventListener("beforeunload", revokePhotoUrls);

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
