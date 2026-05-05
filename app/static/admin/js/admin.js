const API = "/api";
const TOKEN_KEY = "autolux_admin_token";
const USER_KEY = "autolux_admin_user";

const STATUS_LABELS = {
  new: "Жаңа",
  confirmed: "Расталған",
  done: "Өткізілді",
  cancelled: "Бас тартылды",
};

const STATUS_CLASSES = {
  new: "bn",
  confirmed: "bc",
  done: "bd",
  cancelled: "bx",
};

const TYPE_LABELS = {
  sedan: "Седан",
  suv: "Кроссовер",
  sport: "Спорт",
  other: "Басқа",
};

const state = {
  token: window.sessionStorage.getItem(TOKEN_KEY) || "",
  username: window.sessionStorage.getItem(USER_KEY) || "Админ",
  allTD: [],
  allCT: [],
  allCars: [],
  tdFilter: "all",
  editId: null,
  photos: [],
  urlUploadPending: false,
};

const elements = {
  loginWrap: document.getElementById("lw"),
  app: document.getElementById("app"),
  sidebar: document.getElementById("sidebar"),
  sidebarToggle: document.getElementById("sidebarToggle"),
  loginInput: document.getElementById("lu"),
  passwordInput: document.getElementById("lp"),
  loginError: document.getElementById("le"),
  loginButton: document.getElementById("loginBtn"),
  currentDate: document.getElementById("cdate"),
  userName: document.getElementById("sUsr"),
  stats: {
    total: document.getElementById("s1"),
    fresh: document.getElementById("s2"),
    cars: document.getElementById("s3"),
    contacts: document.getElementById("s4"),
  },
  tdBadge: document.getElementById("tdB"),
  dashTestdrives: document.getElementById("dtd"),
  dashContacts: document.getElementById("dct"),
  testdrivesTable: document.getElementById("tdtb"),
  contactsTable: document.getElementById("cttb"),
  carsGrid: document.getElementById("cgrid"),
  modal: document.getElementById("modal"),
  modalTitle: document.getElementById("mttl"),
  saveButton: document.getElementById("svBtn"),
  previews: document.getElementById("pprev"),
  carForm: {
    brand: document.getElementById("fb"),
    name: document.getElementById("fn"),
    type: document.getElementById("ftype"),
    tag: document.getElementById("ftg"),
    price: document.getElementById("fp"),
    fullPrice: document.getElementById("ffp"),
    monthlyPrice: document.getElementById("fm"),
    active: document.getElementById("factive"),
    engine: document.getElementById("fe"),
    speed: document.getElementById("fsp"),
    drive: document.getElementById("fd"),
    fuel: document.getElementById("ffu"),
    tagline: document.getElementById("ftl"),
    features: document.getElementById("ffeat"),
    urlInput: document.getElementById("furl"),
  },
};

function setSidebarOpen(isOpen) {
  if (!elements.sidebar || !elements.sidebarToggle) {
    return;
  }
  elements.sidebar.classList.toggle("open", isOpen);
  elements.sidebarToggle.setAttribute("aria-expanded", String(isOpen));
  elements.sidebarToggle.setAttribute("aria-label", isOpen ? "Менюді жабу" : "Менюді ашу");
}

function toggleSidebar(force) {
  const nextState =
    typeof force === "boolean"
      ? force
      : !elements.sidebar?.classList.contains("open");
  setSidebarOpen(Boolean(nextState));
}

function closeSidebar() {
  setSidebarOpen(false);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return map[char];
  });
}

function sanitizeUrl(url) {
  const value = String(url ?? "").trim();
  if (!value) {
    return "";
  }
  if (value.startsWith("/uploads/")) {
    return value;
  }
  try {
    const parsed = new URL(value, window.location.origin);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.href;
    }
  } catch (_error) {}
  return "";
}

function safePhoneLink(phone) {
  return String(phone ?? "").replace(/[^\d+]/g, "");
}

function formatDate(value) {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return escapeHtml(value);
  }
  return `${date.toLocaleDateString("kk-KZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  })} ${date.toLocaleTimeString("kk-KZ", { hour: "2-digit", minute: "2-digit" })}`;
}

function statusBadge(status) {
  const label = STATUS_LABELS[status] || status || "Белгісіз";
  const badgeClass = STATUS_CLASSES[status] || "bd";
  return `<span class="badge ${badgeClass}">${escapeHtml(label)}</span>`;
}

function emptyRow(columns) {
  return `<tr><td colspan="${columns}" style="text-align:center;padding:22px;color:var(--g)">Мәліметтер жоқ</td></tr>`;
}

function setLoginError(message = "") {
  elements.loginError.textContent = message;
  elements.loginError.style.display = message ? "block" : "none";
}

function setButtonState(button, loading, label) {
  button.disabled = loading;
  button.textContent = label;
}

async function readResponse(response) {
  const text = await response.text();
  let data = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch (_error) {
      throw new Error(`Сервер жауабы дұрыс емес (${response.status})`);
    }
  }

  if (response.status === 401) {
    const error = new Error(data.error || "Сессия мерзімі аяқталды");
    error.unauthorized = true;
    throw error;
  }

  if (!response.ok) {
    throw new Error(data.error || `Сұраныс қатесі (${response.status})`);
  }

  return data;
}

async function apiRequest(path, options = {}, requiresAuth = true) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (requiresAuth && state.token) {
    headers.set("Authorization", `Bearer ${state.token}`);
  }

  try {
    const response = await fetch(`${API}${path}`, { ...options, headers });
    return await readResponse(response);
  } catch (error) {
    if (error.unauthorized) {
      doLogout(false, "Сессия мерзімі аяқталды. Қайта кіріңіз.");
    }
    throw error;
  }
}

function showLogin(message = "") {
  elements.loginWrap.style.display = "flex";
  elements.app.style.display = "none";
  setLoginError(message);
}

function showApp() {
  elements.loginWrap.style.display = "none";
  elements.app.style.display = "block";
}

async function doLogin() {
  const username = elements.loginInput.value.trim();
  const password = elements.passwordInput.value.trim();

  if (!username || !password) {
    setLoginError("Логин мен парольді толтырыңыз.");
    return;
  }

  setLoginError("");
  setButtonState(elements.loginButton, true, "КҮТІҢІЗ...");

  try {
    const data = await apiRequest(
      "/login",
      {
        method: "POST",
        body: JSON.stringify({ username, password }),
      },
      false
    );

    state.token = data.token;
    state.username = data.username || username;
    window.sessionStorage.setItem(TOKEN_KEY, state.token);
    window.sessionStorage.setItem(USER_KEY, state.username);
    elements.userName.textContent = state.username;
    await startApp();
  } catch (error) {
    setLoginError(error.message);
  } finally {
    setButtonState(elements.loginButton, false, "КІРУ →");
  }
}

function doLogout(reload = true, message = "") {
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(USER_KEY);
  state.token = "";
  state.username = "Админ";
  if (reload) {
    window.location.reload();
    return;
  }
  showLogin(message);
}

function nav(page, element) {
  document.querySelectorAll(".pg").forEach((node) => node.classList.remove("on"));
  document.querySelectorAll(".sl").forEach((node) => node.classList.remove("on"));
  document.getElementById(`pg-${page}`).classList.add("on");
  if (element) {
    element.classList.add("on");
  }
  if (window.innerWidth <= 980) {
    closeSidebar();
  }
}

async function startApp() {
  showApp();
  elements.userName.textContent = state.username;
  elements.currentDate.textContent = new Date().toLocaleDateString("kk-KZ", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  await Promise.all([loadStats(), loadTD(), loadCT(), loadCars()]);
}

async function loadStats() {
  const data = await apiRequest("/admin/stats");
  elements.stats.total.textContent = data.td_total;
  elements.stats.fresh.textContent = data.td_new;
  elements.stats.cars.textContent = data.cars;
  elements.stats.contacts.textContent = data.contacts;
  elements.tdBadge.textContent = data.td_new;
  elements.tdBadge.style.display = data.td_new > 0 ? "" : "none";
}

function renderDashboardTestdrives() {
  elements.dashTestdrives.innerHTML =
    state.allTD
      .slice(0, 6)
      .map(
        (item) => `
          <tr>
            <td><b>${escapeHtml(item.name)}</b></td>
            <td><a href="tel:${safePhoneLink(item.phone)}" style="color:var(--blue);text-decoration:none">${escapeHtml(item.phone)}</a></td>
            <td style="font-size:12px">${escapeHtml(item.car || "—")}</td>
            <td>${statusBadge(item.status)}</td>
          </tr>`
      )
      .join("") || emptyRow(4);
}

function renderTD(list) {
  if (!list.length) {
    elements.testdrivesTable.innerHTML = emptyRow(7);
    return;
  }

  elements.testdrivesTable.innerHTML = list
    .map(
      (item) => `
        <tr>
          <td style="color:var(--g)">#${item.id}</td>
          <td><b>${escapeHtml(item.name)}</b></td>
          <td><a href="tel:${safePhoneLink(item.phone)}" style="color:var(--blue);text-decoration:none">${escapeHtml(item.phone)}</a></td>
          <td>${escapeHtml(item.car || "—")}</td>
          <td style="color:var(--g);font-size:11px">${formatDate(item.created)}</td>
          <td>
            <select class="ss" onchange="setS(${item.id},this.value)">
              ${Object.entries(STATUS_LABELS)
                .map(
                  ([value, label]) =>
                    `<option value="${value}"${item.status === value ? " selected" : ""}>${escapeHtml(label)}</option>`
                )
                .join("")}
            </select>
          </td>
          <td><button class="btn br bs" onclick="delTD(${item.id})">Жою</button></td>
        </tr>`
    )
    .join("");
}

async function loadTD() {
  state.allTD = await apiRequest("/admin/testdrives");
  renderDashboardTestdrives();
  renderTD(
    state.tdFilter === "all"
      ? state.allTD
      : state.allTD.filter((item) => item.status === state.tdFilter)
  );
}

function fTD(filter, element) {
  state.tdFilter = filter;
  document.querySelectorAll(".ftb").forEach((node) => node.classList.remove("on"));
  element.classList.add("on");
  renderTD(filter === "all" ? state.allTD : state.allTD.filter((item) => item.status === filter));
}

async function setS(id, status) {
  try {
    await apiRequest(`/admin/testdrives/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    toast("Күй жаңартылды", "tok");
    await Promise.all([loadTD(), loadStats()]);
  } catch (error) {
    toast(error.message, "terr");
  }
}

async function delTD(id) {
  if (!window.confirm("Өтінімді жою керек пе?")) {
    return;
  }

  try {
    await apiRequest(`/admin/testdrives/${id}`, { method: "DELETE" });
    toast("Өтінім жойылды", "tok");
    await Promise.all([loadTD(), loadStats()]);
  } catch (error) {
    toast(error.message, "terr");
  }
}

function renderDashboardContacts() {
  elements.dashContacts.innerHTML =
    state.allCT
      .slice(0, 6)
      .map(
        (item) => `
          <tr>
            <td><b>${escapeHtml(item.name)}</b></td>
            <td style="color:var(--blue)">${escapeHtml(item.phone)}</td>
            <td style="font-size:11px;color:var(--g)">${formatDate(item.created)}</td>
          </tr>`
      )
      .join("") || emptyRow(3);
}

function renderContacts() {
  elements.contactsTable.innerHTML =
    state.allCT
      .map(
        (item) => `
          <tr>
            <td style="color:var(--g)">#${item.id}</td>
            <td><b>${escapeHtml(item.name)}</b></td>
            <td><a href="tel:${safePhoneLink(item.phone)}" style="color:var(--blue);text-decoration:none">${escapeHtml(item.phone)}</a></td>
            <td>${escapeHtml(item.car || "—")}</td>
            <td style="font-size:12px;color:var(--g);max-width:160px">${escapeHtml(item.msg || "—")}</td>
            <td style="font-size:11px;color:var(--g)">${formatDate(item.created)}</td>
          </tr>`
      )
      .join("") || emptyRow(6);
}

async function loadCT() {
  state.allCT = await apiRequest("/admin/contacts");
  renderContacts();
  renderDashboardContacts();
}

function renderCars() {
  if (!state.allCars.length) {
    elements.carsGrid.innerHTML =
      '<div style="grid-column:1/-1;text-align:center;padding:50px;color:var(--g)">Машиналар жоқ</div>';
    return;
  }

  elements.carsGrid.innerHTML = state.allCars
    .map((car) => {
      const image = sanitizeUrl(Array.isArray(car.photos) ? car.photos[0] : "");
      const label = `${car.brand || ""} ${car.name || ""}`.trim();
      return `
        <div class="cc${car.active ? "" : " off"}">
          ${
            image
              ? `<img class="ci" src="${image}" alt="${escapeHtml(label)}" onerror="this.style.display='none'">`
              : `<div class="cp"><svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21,15 16,10 5,21"/></svg></div>`
          }
          <div class="cb">
            <div class="cbr">${escapeHtml(car.brand || "AutoLux")}</div>
            <div class="cn">${escapeHtml(car.name || "Модель")}</div>
            <div class="cpr">${escapeHtml(car.price || "—")} ₸</div>
            <div class="ct">${escapeHtml(TYPE_LABELS[car.type] || car.type || "Белгісіз")} • ID:${car.id} • ${car.active ? "Белсенді" : "Жасырын"}</div>
            <div class="cbt">
              <button class="btn bb bs" onclick="openM(${car.id})" style="flex:1">Өңдеу</button>
              <button class="btn br bs" onclick="delCar(${car.id})">Жою</button>
            </div>
          </div>
        </div>`;
    })
    .join("");
}

async function loadCars() {
  state.allCars = await apiRequest("/admin/cars");
  renderCars();
}

function resetCarForm() {
  state.editId = null;
  state.photos = [];
  elements.modalTitle.textContent = "ЖАҢА МАШИНА ҚОСУ";
  elements.carForm.brand.value = "";
  elements.carForm.name.value = "";
  elements.carForm.type.value = "sedan";
  elements.carForm.tag.value = "";
  elements.carForm.price.value = "";
  elements.carForm.fullPrice.value = "";
  elements.carForm.monthlyPrice.value = "";
  elements.carForm.active.value = "1";
  elements.carForm.engine.value = "";
  elements.carForm.speed.value = "";
  elements.carForm.drive.value = "";
  elements.carForm.fuel.value = "";
  elements.carForm.tagline.value = "";
  elements.carForm.features.value = "";
  elements.carForm.urlInput.value = "";
  elements.previews.innerHTML = "";
}

function renderP() {
  elements.previews.innerHTML = state.photos
    .map((photo, index) => {
      const safePhoto = sanitizeUrl(photo);
      return `
        <div class="pt2">
          <img src="${safePhoto}" alt="car photo" style="background:#1a1a2e">
          <button class="px" onclick="removePhoto(${index})">✕</button>
        </div>`;
    })
    .join("");
}

function removePhoto(index) {
  state.photos.splice(index, 1);
  renderP();
}

async function openM(id = null) {
  resetCarForm();
  state.editId = id;

  if (id !== null) {
    elements.modalTitle.textContent = "МАШИНАНЫ ӨҢДЕУ";
    try {
      const car = await apiRequest(`/admin/cars/${id}`);
      elements.carForm.brand.value = car.brand || "";
      elements.carForm.name.value = car.name || "";
      elements.carForm.type.value = car.type || "sedan";
      elements.carForm.tag.value = car.tag || "";
      elements.carForm.price.value = car.price || "";
      elements.carForm.fullPrice.value = car.fullPrice || "";
      elements.carForm.monthlyPrice.value = car.monthlyPrice || "";
      elements.carForm.active.value = car.active ? "1" : "0";
      elements.carForm.engine.value = car.engine || "";
      elements.carForm.speed.value = car.speed || "";
      elements.carForm.drive.value = car.drive || "";
      elements.carForm.fuel.value = car.fuel || "";
      elements.carForm.tagline.value = car.tagline || "";
      elements.carForm.features.value = Array.isArray(car.features) ? car.features.join("\n") : "";
      state.photos = Array.isArray(car.photos) ? [...car.photos] : [];
      renderP();
    } catch (error) {
      toast(error.message, "terr");
      return;
    }
  }

  elements.modal.classList.add("on");
}

function closeM() {
  elements.modal.classList.remove("on");
  resetCarForm();
}

async function addUrl() {
  const value = sanitizeUrl(elements.carForm.urlInput.value.trim());
  if (!value) {
    toast("Сурет сілтемесі жарамсыз", "terr");
    return;
  }

  if (state.urlUploadPending) {
    return;
  }

  state.urlUploadPending = true;

  try {
    const data = await apiRequest("/admin/upload-url", {
      method: "POST",
      body: JSON.stringify({ url: value }),
    });
    state.photos.push(data.url);
    elements.carForm.urlInput.value = "";
    renderP();
    toast("Фото сілтеме арқылы қосылды", "tok");
  } catch (error) {
    toast(error.message, "terr");
  } finally {
    state.urlUploadPending = false;
  }
}

function upFiles(input) {
  Array.from(input.files).forEach((file) => {
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const data = await apiRequest("/admin/upload", {
          method: "POST",
          body: JSON.stringify({
            image: event.target.result,
            ext: file.name.split(".").pop().toLowerCase(),
          }),
        });
        state.photos.push(data.url);
        renderP();
        toast("Фото жүктелді", "tok");
      } catch (error) {
        toast(error.message, "terr");
      }
    };
    reader.readAsDataURL(file);
  });
  input.value = "";
}

async function saveCar() {
  const brand = elements.carForm.brand.value.trim();
  const name = elements.carForm.name.value.trim();
  const price = elements.carForm.price.value.trim();

  if (!brand || !name || !price) {
    toast("Бренд, модель, баға міндетті", "terr");
    return;
  }

  const payload = {
    brand,
    name,
    type: elements.carForm.type.value,
    tag: elements.carForm.tag.value || "ЖАҢА",
    price,
    full_price: elements.carForm.fullPrice.value.trim() || price,
    monthly_price: elements.carForm.monthlyPrice.value.trim(),
    engine: elements.carForm.engine.value.trim(),
    speed: elements.carForm.speed.value.trim(),
    drive: elements.carForm.drive.value.trim(),
    fuel: elements.carForm.fuel.value.trim(),
    tagline: elements.carForm.tagline.value.trim(),
    features: elements.carForm.features.value
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean),
    photos: state.photos,
    is_active: Number(elements.carForm.active.value),
  };

  setButtonState(elements.saveButton, true, "САҚТАЛУДА...");

  try {
    if (state.editId !== null) {
      await apiRequest(`/admin/cars/${state.editId}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      toast("Машина жаңартылды", "tok");
    } else {
      await apiRequest("/admin/cars", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      toast("Жаңа машина қосылды", "tok");
    }
    closeM();
    await Promise.all([loadCars(), loadStats()]);
  } catch (error) {
    toast(error.message, "terr");
  } finally {
    setButtonState(elements.saveButton, false, "САҚТАУ");
  }
}

async function delCar(id) {
  if (!window.confirm("Осы машинаны жою керек пе?")) {
    return;
  }
  try {
    await apiRequest(`/admin/cars/${id}`, { method: "DELETE" });
    toast("Машина жойылды", "tok");
    await Promise.all([loadCars(), loadStats()]);
  } catch (error) {
    toast(error.message, "terr");
  }
}

function search(tableId, query) {
  document.querySelectorAll(`#${tableId} tr`).forEach((row) => {
    row.style.display = row.textContent.toLowerCase().includes(query.toLowerCase()) ? "" : "none";
  });
}

function toast(message, cls = "tok") {
  const node = document.getElementById("toast");
  node.textContent = message;
  node.className = `toast ${cls} show`;
  window.clearTimeout(node._timer);
  node._timer = window.setTimeout(() => node.classList.remove("show"), 3000);
}

function init() {
  elements.modal.addEventListener("click", (event) => {
    if (event.target === elements.modal) {
      closeM();
    }
  });

  elements.carForm.urlInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addUrl();
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 980) {
      closeSidebar();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSidebar();
    }
  });

  if (state.token) {
    startApp().catch((error) => {
      showLogin(error.message);
    });
  } else {
    showLogin();
  }
}

window.doLogin = doLogin;
window.doLogout = doLogout;
window.nav = nav;
window.toggleSidebar = toggleSidebar;
window.fTD = fTD;
window.setS = setS;
window.delTD = delTD;
window.openM = openM;
window.closeM = closeM;
window.addUrl = addUrl;
window.upFiles = upFiles;
window.saveCar = saveCar;
window.delCar = delCar;
window.search = search;
window.removePhoto = removePhoto;

init();
