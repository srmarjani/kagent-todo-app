const API = "/api/todos";

const form = document.getElementById("add-form");
const titleInput = document.getElementById("title-input");
const dueInput = document.getElementById("due-input");
const filterSelect = document.getElementById("filter-select");
const list = document.getElementById("todo-list");
const emptyMessage = document.getElementById("empty-message");
const errorBox = document.getElementById("error");

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

function renderTodo(todo) {
  const item = document.createElement("li");
  item.id = "todo-" + todo.id;
  if (todo.done) item.className = "done";

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
  due.textContent = todo.due_date ? "due " + todo.due_date : "";

  const remove = document.createElement("button");
  remove.id = "delete-" + todo.id;
  remove.type = "button";
  remove.textContent = "Delete";
  remove.addEventListener("click", () => deleteTodo(todo.id));

  item.append(checkbox, title, due, remove);
  return item;
}

async function loadTodos() {
  try {
    const todos = await request(API + "?status=" + encodeURIComponent(filterSelect.value));
    list.replaceChildren(...todos.map(renderTodo));
    emptyMessage.hidden = todos.length > 0;
    showError("");
  } catch (err) {
    showError("Could not load todos: " + err.message);
  }
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

loadTodos();
