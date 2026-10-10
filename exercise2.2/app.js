"use strict";

const allowedCategories = ["Hardware", "Software", "Network", "Account/Login", "General"];
const allowedUrgencies = ["Low", "Medium", "High", "Critical"];
const allowedContacts = ["Email", "Phone", "In-person"];

// Demonstration-only data. No real user or campus ticket information is stored here.
const tickets = [
  { id: "HD-2048", title: "Wi-Fi drops in the library", category: "Network", status: "In progress", statusClass: "progress", updated: "12 min ago" },
  { id: "HD-2047", title: "Unable to install design software", category: "Software", status: "Open", statusClass: "", updated: "38 min ago" },
  { id: "HD-2046", title: "Reset campus account password", category: "Account/Login", status: "Waiting on user", statusClass: "waiting", updated: "1 hr ago" },
  { id: "HD-2045", title: "Projector not displaying image", category: "Hardware", status: "Open", statusClass: "", updated: "2 hrs ago" },
  { id: "HD-2044", title: "Question about printing credits", category: "General", status: "Resolved", statusClass: "", updated: "Yesterday" },
  { id: "HD-2043", title: "VPN connection times out", category: "Network", status: "In progress", statusClass: "progress", updated: "Yesterday" }
];

const form = document.querySelector("#request-form");
const formStatus = document.querySelector("#form-status");
const summary = document.querySelector("#summary-content");
const description = document.querySelector("#description");
const charCount = document.querySelector("#char-count");
const ticketRows = document.querySelector("#ticket-rows");
const ticketSearch = document.querySelector("#ticket-search");
const ticketFilter = document.querySelector("#ticket-filter");
let submittedTickets = [];

function setError(field, message) {
  field.classList.toggle("invalid", Boolean(message));
  const error = field.querySelector(".field-error");
  if (error) error.textContent = message;
}

function validateForm() {
  let firstInvalid = null;
  const checks = [
    { id: "category", valid: allowedCategories.includes(form.elements.category.value), message: "Choose a category from the list." },
    { id: "urgency", valid: allowedUrgencies.includes(form.elements.urgency.value), message: "Choose an urgency level." },
    { id: "title", valid: form.elements.title.value.trim().length >= 5 && form.elements.title.value.trim().length <= 100, message: "Enter a title between 5 and 100 characters." },
    { id: "description", valid: description.value.trim().length >= 20 && description.value.trim().length <= 2000, message: "Enter a description between 20 and 2,000 characters." }
  ];
  checks.forEach((check) => {
    const control = document.getElementById(check.id);
    const field = control.closest(".field");
    setError(field, check.valid ? "" : check.message);
    if (!check.valid && !firstInvalid) firstInvalid = control;
  });

  const contact = form.querySelector('input[name="contact"]:checked');
  const contactField = form.querySelector(".contact-field");
  const contactValid = Boolean(contact && allowedContacts.includes(contact.value));
  setError(contactField, contactValid ? "" : "Choose a preferred contact method.");
  if (!contactValid && !firstInvalid) firstInvalid = form.querySelector('input[name="contact"]');
  return { valid: !firstInvalid, firstInvalid };
}

description.addEventListener("input", () => {
  charCount.textContent = `${description.value.length.toLocaleString()} / 2,000`;
  if (description.closest(".field").classList.contains("invalid")) validateForm();
});
form.addEventListener("input", (event) => {
  if (event.target.name === "contact" || event.target.matches("input, select, textarea")) {
    formStatus.textContent = "";
    formStatus.classList.remove("error");
  }
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const result = validateForm();
  if (!result.valid) {
    formStatus.className = "form-status error";
    formStatus.textContent = "Please check the highlighted fields and try again.";
    result.firstInvalid.focus();
    return;
  }

  const requestId = `HD-${String(Date.now()).slice(-6)}`;
  const request = {
    id: requestId,
    category: form.elements.category.value,
    urgency: form.elements.urgency.value,
    title: form.elements.title.value.trim(),
    description: form.elements.description.value.trim(),
    contact: form.querySelector('input[name="contact"]:checked').value
  };
  submittedTickets.unshift({ id: requestId, title: request.title, category: request.category,
    status: "Submitted · demo", statusClass: "waiting", updated: "Just now" });
  renderTickets();

  // Render user-provided content only as text; never interpret it as HTML.
  summary.replaceChildren();
  summary.classList.add("has-summary");
  const id = document.createElement("p");
  id.className = "summary-id";
  id.textContent = `REQUEST ${request.id} · RECEIVED`;
  const title = document.createElement("h3");
  title.className = "summary-title";
  title.textContent = request.title;
  const details = document.createElement("div");
  details.className = "summary-details";
  [["Category", request.category], ["Urgency", request.urgency], ["Contact", request.contact], ["Next step", "Team review"]].forEach(([label, value]) => {
    const item = document.createElement("div");
    item.className = "summary-detail";
    const caption = document.createElement("span");
    caption.textContent = label;
    const detail = document.createElement("strong");
    detail.textContent = value;
    item.append(caption, detail);
    details.append(item);
  });
  summary.append(id, title, details);
  formStatus.className = "form-status";
  formStatus.textContent = `Request ${request.id} submitted. Your confirmation is shown in the summary panel.`;
  form.reset();
  charCount.textContent = "0 / 2,000";
  document.querySelectorAll(".field.invalid").forEach((field) => setError(field, ""));
  formStatus.focus();
});

function renderTickets() {
  const term = ticketSearch.value.trim().toLocaleLowerCase();
  const category = ticketFilter.value;
  const visible = [...submittedTickets, ...tickets].filter((ticket) => {
    const matchesCategory = category === "all" || ticket.category === category;
    const matchesSearch = `${ticket.id} ${ticket.title} ${ticket.category} ${ticket.status}`.toLocaleLowerCase().includes(term);
    return matchesCategory && matchesSearch;
  });
  ticketRows.replaceChildren();
  visible.forEach((ticket) => {
    const row = document.createElement("tr");
    const requestCell = document.createElement("td");
    requestCell.textContent = `${ticket.id} · ${ticket.title}`;
    const categoryCell = document.createElement("td");
    const categoryTag = document.createElement("span");
    categoryTag.className = "category-tag";
    categoryTag.textContent = ticket.category;
    categoryCell.append(categoryTag);
    const statusCell = document.createElement("td");
    const statusTag = document.createElement("span");
    statusTag.className = `status-tag ${ticket.statusClass}`.trim();
    statusTag.textContent = ticket.status;
    statusCell.append(statusTag);
    const updatedCell = document.createElement("td");
    updatedCell.textContent = ticket.updated;
    row.append(requestCell, categoryCell, statusCell, updatedCell);
    ticketRows.append(row);
  });
  document.querySelector("#empty-tickets").hidden = visible.length > 0;
  document.querySelector("#ticket-count").textContent = `${visible.length} ${visible.length === 1 ? "request" : "requests"}`;
}

ticketSearch.addEventListener("input", renderTickets);
ticketFilter.addEventListener("change", renderTickets);
renderTickets();
