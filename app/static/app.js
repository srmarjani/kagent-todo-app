const API = "/api/todos";

const form = document.getElementById("add-form");
const titleInput = document.getElementById("title-input");
const dueInput = document.getElementById("due-input");
const filterSelect = document.getElementById("filter-select");
const clearButton = document.getElementById("clear-completed");
const list = document.getElementById("todo-list");
const emptyMessage = document.getElementById("empty-message");
const errorBox = document.getElementById("error");
const statsBox = document.getElementById("stats");

function showError(message) {
  errorBox.textContent = message || "";
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error("Request failed (" + response.status + ")");
  }
  return response.status === 204 ? null : response.json();
}

// Today's date as YYYY-MM-DD in the browser's local time zone.
function todayString() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return now.getFullYear() + "-" + month + "-" + day;
}

// An open todo is overdue when its due date is before today.
// YYYY-MM-DD strings compare correctly as plain strings.
function isOverdue(todo, today) {
  return !todo.done && !!todo.due_date && todo.due_date < today;
}

function renderTodo(todo, today) {
  const overdue = isOverdue(todo, today);

  const item = document.createElement("li");
  item.id = "todo-" + todo.id;
  const classes = [];
  if (todo.done) classes.push("done");
  if (overdue) classes.push("overdue");
  item.className = classes.join(" ");

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.id = "done-" + todo.id;
  checkbox.checked = todo.done;
  checkbox.setAttribute("aria-label", "Done: " + todo.title);
  checkbox.addEventListener("change", () => toggleTodo(todo.id, checkbox.checked));

  const title = document.createElement("span");
  title.className = "todo-title";
  title.textContent = todo.title;

  const due = document.createElement("span");
  due.className = "todo-due";
  due.id = "due-" + todo.id;
  if (todo.due_date) {
    due.textContent = "due " + todo.due_date + (overdue ? " (overdue)" : "");
  }

  const remove = document.createElement("button");
  remove.id = "delete-" + todo.id;
  remove.type = "button";
  remove.textContent = "Delete";
  remove.addEventListener("click", () => deleteTodo(todo.id));

  item.append(checkbox, title, due, remove);
  return item;
}

// Show "N open · M done" in the header, from GET /api/todos/stats.
async function updateStats() {
  try {
    const stats = await request(API + "/stats");
    statsBox.textContent = stats.open + " open · " + stats.done + " done";
  } catch (err) {
    statsBox.textContent = "– open · – done";
  }
}

// Enable "Clear completed" only when at least one todo is done.
// Asks the API for done todos so it also works while the filter is "Open".
async function updateClearButton() {
  try {
    const doneTodos = await request(API + "?status=done");
    clearButton.disabled = doneTodos.length === 0;
  } catch (err) {
    clearButton.disabled = true;
  }
}

// Every add, toggle, delete and clear ends in loadTodos(), so the counts
// are refreshed here, in one place.
async function loadTodos() {
  try {
    const todos = await request(API + "?status=" + encodeURIComponent(filterSelect.value));
    const today = todayString();
    list.replaceChildren(...todos.map((todo) => renderTodo(todo, today)));
    emptyMessage.hidden = todos.length > 0;
    showError("");
  } catch (err) {
    showError("Could not load todos: " + err.message);
  }
  await updateStats();
  await updateClearButton();
}

async function toggleTodo(id, done) {
  try {
    await request(API + "/" + id, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ done: done }),
    });
  } catch (err) {
    showError("Could not update todo: " + err.message);
  }
  await loadTodos();
}

async function deleteTodo(id) {
  try {
    await request(API + "/" + id, { method: "DELETE" });
  } catch (err) {
    showError("Could not delete todo: " + err.message);
  }
  await loadTodos();
}

async function clearCompleted() {
  try {
    await request(API + "?status=done", { method: "DELETE" });
  } catch (err) {
    showError("Could not clear completed todos: " + err.message);
  }
  await loadTodos();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = titleInput.value.trim();
  if (!title) {
    showError("Title must not be empty.");
    return;
  }
  const body = { title: title };
  if (dueInput.value) body.due_date = dueInput.value;
  try {
    await request(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    form.reset();
    showError("");
  } catch (err) {
    showError("Could not add todo: " + err.message);
    return;
  }
  await loadTodos();
});

filterSelect.addEventListener("change", loadTodos);
clearButton.addEventListener("click", clearCompleted);

loadTodos();
