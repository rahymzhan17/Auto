const API = "/api";
const DEFAULT_IMAGE =
  "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=900&q=80";

const SLIDES = [
  "https://images.unsplash.com/photo-1555215695-3004980ad54e?w=1920&q=85",
  "https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?w=1920&q=85",
  "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1920&q=85",
  "https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=1920&q=85",
  "https://images.unsplash.com/photo-1525609004556-c46c7d6cf023?w=1920&q=85",
  "https://images.unsplash.com/photo-1493238792000-8113da705763?w=1920&q=85",
];

const ICONS = {
  engine:
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><line x1="12" y1="12" x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/></svg>',
  speed:
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>',
  fuel:
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 22V6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v16"/><line x1="3" y1="22" x2="14" y2="22"/></svg>',
  drive:
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>',
  seats:
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
  year:
    '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
};

const state = {
  cars: [],
  currentCar: null,
  currentFilter: "all",
  galleryIndex: 0,
  slideIndex: 0,
};

const elements = {
  siteNav: document.getElementById("siteNav"),
  navToggle: document.getElementById("navToggle"),
  carsGrid: document.getElementById("carsGrid"),
  heroSlides: document.getElementById("heroSlides"),
  slideDots: document.getElementById("slideDots"),
  slideProgress: document.getElementById("slideProgress"),
  particles: document.getElementById("particles"),
  mainPage: document.getElementById("mainPage"),
  detailPage: document.getElementById("detailPage"),
  detailContent: document.getElementById("detailContent"),
  modal: document.getElementById("modal"),
  contactName: document.getElementById("contactName"),
  contactPhone: document.getElementById("contactPhone"),
  contactCar: document.getElementById("contactCar"),
  contactMessage: document.getElementById("contactMessage"),
  contactSubmit: document.getElementById("contactSubmit"),
  contactStatus: document.getElementById("contactStatus"),
  modalName: document.getElementById("modalName"),
  modalPhone: document.getElementById("modalPhone"),
  modalCar: document.getElementById("modalCar"),
  modalSubmit: document.getElementById("modalSubmit"),
  modalStatus: document.getElementById("modalStatus"),
};

function setNavState(isOpen) {
  if (!elements.siteNav || !elements.navToggle) {
    return;
  }
  elements.siteNav.classList.toggle("nav-open", isOpen);
  elements.navToggle.setAttribute("aria-expanded", String(isOpen));
  elements.navToggle.setAttribute("aria-label", isOpen ? "Менюді жабу" : "Менюді ашу");
}

function toggleNav(force) {
  const nextState =
    typeof force === "boolean"
      ? force
      : !elements.siteNav?.classList.contains("nav-open");
  setNavState(Boolean(nextState));
}

function closeNav() {
  setNavState(false);
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
    return DEFAULT_IMAGE;
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
  return DEFAULT_IMAGE;
}

function safeText(value, fallback = "—") {
  const cleaned = String(value ?? "").trim();
  return escapeHtml(cleaned || fallback);
}

function safePhoneLink(phone) {
  const cleaned = String(phone ?? "").replace(/[^\d+]/g, "");
  return cleaned || "";
}

function selectedCarLabel(car) {
  return [car?.brand, car?.name].filter(Boolean).join(" ").trim();
}

function buildCarOptions(selectedValue = "", includePlaceholder = true) {
  const options = [];
  if (includePlaceholder) {
    options.push('<option value="">Моделді таңдаңыз</option>');
  }

  state.cars.forEach((car) => {
    const label = selectedCarLabel(car);
    if (!label) {
      return;
    }
    const selected = label === selectedValue ? " selected" : "";
    options.push(
      `<option value="${escapeHtml(label)}"${selected}>${escapeHtml(label)}</option>`
    );
  });

  return options.join("");
}

function populateCarSelects(selectedValue = "") {
  const fallbackOptions = '<option value="">Моделді таңдаңыз</option>';
  elements.contactCar.innerHTML = state.cars.length
    ? buildCarOptions("", true)
    : fallbackOptions;
  elements.modalCar.innerHTML = state.cars.length
    ? buildCarOptions(selectedValue, true)
    : fallbackOptions;
}

function getCarPhotos(car) {
  const photos = Array.isArray(car?.photos) ? car.photos : [];
  const safePhotos = photos.map(sanitizeUrl).filter(Boolean);
  return safePhotos.length ? safePhotos : [DEFAULT_IMAGE];
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  const text = await response.text();
  let data = {};

  if (text) {
    try {
      data = JSON.parse(text);
    } catch (_error) {
      throw new Error(`Сервер жауабы дұрыс емес (${response.status})`);
    }
  }

  if (!response.ok) {
    throw new Error(data.error || `Сұраныс қатесі (${response.status})`);
  }
  return data;
}

function setStatus(element, message, type = "") {
  element.textContent = message || "";
  element.className = `form-status ${type}`.trim();
}

function setButtonState(button, loading, label) {
  button.disabled = loading;
  button.textContent = label;
}

function initHero() {
  SLIDES.forEach((url, index) => {
    const slide = document.createElement("div");
    slide.className = `hero-slide${index === 0 ? " active" : ""}`;
    slide.style.backgroundImage = `url(${url})`;
    elements.heroSlides.appendChild(slide);

    const dot = document.createElement("button");
    dot.type = "button";
    dot.className = `slide-dot${index === 0 ? " active" : ""}`;
    dot.addEventListener("click", () => goSlide(index));
    elements.slideDots.appendChild(dot);
  });

  elements.slideProgress.style.transition = "width 5s linear";
  elements.slideProgress.style.width = "100%";
  window.setInterval(() => goSlide(state.slideIndex + 1), 5000);
}

function goSlide(nextIndex) {
  const slides = elements.heroSlides.querySelectorAll(".hero-slide");
  const dots = elements.slideDots.querySelectorAll(".slide-dot");

  if (!slides.length || !dots.length) {
    return;
  }

  slides[state.slideIndex].classList.remove("active");
  dots[state.slideIndex].classList.remove("active");
  state.slideIndex = (nextIndex + SLIDES.length) % SLIDES.length;
  slides[state.slideIndex].classList.add("active");
  dots[state.slideIndex].classList.add("active");

  elements.slideProgress.style.transition = "none";
  elements.slideProgress.style.width = "0%";
  window.setTimeout(() => {
    elements.slideProgress.style.transition = "width 5s linear";
    elements.slideProgress.style.width = "100%";
  }, 30);
}

function initParticles() {
  for (let index = 0; index < 30; index += 1) {
    const particle = document.createElement("div");
    particle.className = "particle";
    particle.style.cssText = `
      left:${Math.random() * 100}%;
      animation-duration:${8 + Math.random() * 12}s;
      animation-delay:${Math.random() * 10}s;
      background:${Math.random() > 0.5 ? "#00d4ff" : "#b44fff"};
      width:${1 + Math.random() * 3}px;
      height:${1 + Math.random() * 3}px;
    `;
    elements.particles.appendChild(particle);
  }
}

function observeReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
}

async function loadCars() {
  elements.carsGrid.innerHTML =
    '<div style="grid-column:1/-1;text-align:center;padding:70px 20px;color:rgba(255,255,255,0.4)">Каталог жүктелуде...</div>';

  try {
    state.cars = await apiRequest("/cars");
    renderCars(state.currentFilter);
    populateCarSelects();
    observeReveal();
  } catch (error) {
    elements.carsGrid.innerHTML =
      `<div style="grid-column:1/-1;text-align:center;padding:70px 20px;color:rgba(255,255,255,0.4)">
        <p style="font-size:16px;margin-bottom:12px">${escapeHtml(error.message)}</p>
        <code style="background:rgba(255,255,255,0.07);padding:8px 16px;border-radius:8px;font-size:13px">python server.py</code>
      </div>`;
    populateCarSelects();
  }
}

function renderCars(filter) {
  state.currentFilter = filter || "all";
  const cars =
    state.currentFilter === "all"
      ? state.cars
      : state.cars.filter((car) => car.type === state.currentFilter);

  if (!cars.length) {
    elements.carsGrid.innerHTML =
      '<div style="grid-column:1/-1;text-align:center;padding:60px;color:rgba(255,255,255,0.4)">Машиналар табылмады</div>';
    return;
  }

  elements.carsGrid.innerHTML = "";
  cars.forEach((car, index) => {
    const card = document.createElement("div");
    const photo = getCarPhotos(car)[0];
    const carLabel = selectedCarLabel(car) || "Автомобиль";

    card.className = "car-card reveal";
    card.style.transitionDelay = `${index * 0.08}s`;
    card.innerHTML = `
      <div class="car-card-img">
        <div class="car-badge">${safeText(car.tag, "ЖАҢА")}</div>
        <img src="${photo}" alt="${escapeHtml(carLabel)}" loading="lazy"
             onerror="this.src='${DEFAULT_IMAGE}'">
        <div class="car-card-img-overlay"></div>
      </div>
      <div class="car-card-body">
        <div class="car-brand">${safeText(car.brand)}</div>
        <div class="car-name">${safeText(car.name)}</div>
        <div class="car-specs">
          <div class="spec"><span class="spec-val">${safeText(car.engine)}</span><span class="spec-label">Қозғалтқыш</span></div>
          <div class="spec"><span class="spec-val">${safeText(car.speed)}</span><span class="spec-label">0-100 км/с</span></div>
          <div class="spec"><span class="spec-val">${safeText(car.drive)}</span><span class="spec-label">Жетек</span></div>
        </div>
        <div class="car-card-footer">
          <div class="car-price"><small>Бастап</small>${safeText(car.price)} ₸</div>
          <button type="button" class="btn-detail" onclick="openDetail(${Number(car.id)})">
            Толығырақ
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12,5 19,12 12,19"/></svg>
          </button>
        </div>
      </div>`;
    elements.carsGrid.appendChild(card);
  });

  observeReveal();
}

function filterCars(button, filter) {
  document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  renderCars(filter);
}

function showPage(page) {
  closeNav();
  elements.mainPage.classList.toggle("active", page === "main");
  elements.detailPage.classList.toggle("active", page === "detail");
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (page === "main") {
    observeReveal();
  }
}

function renderDetail(car) {
  const photos = getCarPhotos(car);
  const specs = Array.isArray(car.fullSpecs) ? car.fullSpecs : [];
  const features = Array.isArray(car.features) ? car.features : [];
  const credit = Array.isArray(car.credit) ? car.credit : [];
  const carLabel = selectedCarLabel(car) || "Автомобиль";

  elements.detailContent.innerHTML = `
    <div class="detail-hero">
      <div class="gallery">
        <div class="gallery-main">
          <img id="mImg" src="${photos[0]}" alt="${escapeHtml(carLabel)}" onerror="this.src='${DEFAULT_IMAGE}'">
          <div class="gallery-main-overlay"></div>
          <div class="gallery-nav">
            <button type="button" class="gnav-btn" onclick="gNav(-1)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15,18 9,12 15,6"/></svg></button>
            <button type="button" class="gnav-btn" onclick="gNav(1)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9,18 15,12 9,6"/></svg></button>
          </div>
        </div>
        <div class="gallery-thumbs">
          ${photos
            .map(
              (photo, index) =>
                `<div class="thumb ${index === 0 ? "active" : ""}" onclick="gSet(${index})"><img src="${photo}" alt="${escapeHtml(carLabel)}"></div>`
            )
            .join("")}
        </div>
      </div>
      <div class="detail-info">
        <button type="button" class="detail-back" onclick="showPage('main')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15,18 9,12 15,6"/></svg>
          Каталогқа оралу
        </button>
        <div class="detail-badge">${safeText(car.tag, "ЖАҢА")}</div>
        <div class="detail-brand">${safeText(car.brand)}</div>
        <div class="detail-name">${safeText(car.name)}</div>
        <div class="detail-tagline">${safeText(car.tagline, "AutoLux таңдауы")}</div>
        <div class="detail-price-block">
          <div class="detail-price-label">Бастапқы баға</div>
          <div class="detail-price">${safeText(car.fullPrice || car.price)} ₸</div>
          <div class="detail-price-note">Немесе айына ${safeText(car.monthlyPrice, "—")} ₸ - кредитпен</div>
        </div>
        <div class="spec-grid">
          ${specs
            .slice(0, 4)
            .map(
              (spec) => `
                <div class="spec-box">
                  <div class="spec-box-icon">${ICONS[spec.k] || ICONS.engine}</div>
                  <div><div class="spec-box-val">${safeText(spec.v)}</div><div class="spec-box-label">${safeText(spec.l)}</div></div>
                </div>`
            )
            .join("")}
        </div>
        <div class="detail-btns">
          <button type="button" class="btn-order" onclick="openModal()">ТАПСЫРЫС БЕРУ</button>
          <button type="button" class="btn-test" onclick="openModal()">ТЕСТ ДРАЙВ</button>
        </div>
      </div>
    </div>
    <div class="detail-tabs-section">
      <div class="detail-tabs">
        <button type="button" class="dtab active" onclick="dTab(this,'specs')">Толық сипаттама</button>
        <button type="button" class="dtab" onclick="dTab(this,'features')">Жабдықтау</button>
        <button type="button" class="dtab" onclick="dTab(this,'credit')">Кредит</button>
      </div>
      <div id="tab-specs" class="dtab-content active">
        <div class="full-specs-grid">
          ${specs
            .map(
              (spec) => `
                <div class="fspec-item">
                  <div class="fspec-icon">${ICONS[spec.k] || ICONS.engine}</div>
                  <div><div class="fspec-val">${safeText(spec.v)}</div><div class="fspec-label">${safeText(spec.l)}</div></div>
                </div>`
            )
            .join("")}
        </div>
      </div>
      <div id="tab-features" class="dtab-content">
        <div class="features-list">
          ${
            features.length
              ? features
                  .map(
                    (feature) => `
                      <div class="feat-item">
                        <div class="feat-check"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20,6 9,17 4,12"/></svg></div>
                        <span class="feat-text">${safeText(feature)}</span>
                      </div>`
                  )
                  .join("")
              : '<p style="color:rgba(255,255,255,0.4);padding:20px">Жабдықтау тізімі жоқ</p>'
          }
        </div>
      </div>
      <div id="tab-credit" class="dtab-content">
        <div class="credit-card-d">
          <h4>КРЕДИТ ЕСЕБІ</h4>
          <div class="credit-rows">
            ${credit
              .map(
                (item) => `<div class="credit-row"><span>${safeText(item.l)}</span><span>${safeText(item.v)}</span></div>`
              )
              .join("")}
          </div>
        </div>
        <button type="button" class="btn-submit" style="max-width:320px;margin-top:20px" onclick="openModal()">КРЕДИТКЕ ӨТІНІМ БЕРУ →</button>
      </div>
    </div>`;

  showPage("detail");
}

async function openDetail(carId) {
  let car = state.cars.find((item) => item.id === carId);
  if (!car) {
    try {
      car = await apiRequest(`/cars/${carId}`);
    } catch (error) {
      window.alert(error.message);
      return;
    }
  }

  state.currentCar = car;
  state.galleryIndex = 0;
  populateCarSelects(selectedCarLabel(car));
  renderDetail(car);
}

function gNav(direction) {
  const total = getCarPhotos(state.currentCar).length;
  gSet((state.galleryIndex + direction + total) % total);
}

function gSet(index) {
  state.galleryIndex = index;
  const photos = getCarPhotos(state.currentCar);
  const image = document.getElementById("mImg");
  if (!image) {
    return;
  }

  image.style.opacity = "0";
  window.setTimeout(() => {
    image.src = photos[index];
    image.style.opacity = "1";
  }, 180);
  image.style.transition = "opacity 0.22s";
  document.querySelectorAll(".thumb").forEach((thumb, thumbIndex) => {
    thumb.classList.toggle("active", thumbIndex === index);
  });
}

function dTab(button, tabId) {
  document.querySelectorAll(".dtab").forEach((tab) => tab.classList.remove("active"));
  document.querySelectorAll(".dtab-content").forEach((content) =>
    content.classList.remove("active")
  );
  button.classList.add("active");
  document.getElementById(`tab-${tabId}`).classList.add("active");
}

function openModal() {
  closeNav();
  const selected = state.currentCar ? selectedCarLabel(state.currentCar) : "";
  populateCarSelects(selected);
  elements.modal.classList.add("open");
}

function closeModal() {
  elements.modal.classList.remove("open");
}

async function submitForm() {
  const payload = {
    name: elements.contactName.value.trim(),
    phone: elements.contactPhone.value.trim(),
    car: elements.contactCar.value.trim(),
    message: elements.contactMessage.value.trim(),
  };

  if (!payload.name || !payload.phone) {
    setStatus(elements.contactStatus, "Аты-жөніңіз бен телефон нөміріңізді толтырыңыз.", "error");
    return;
  }

  setStatus(elements.contactStatus, "", "");
  setButtonState(elements.contactSubmit, true, "ЖІБЕРІЛУДЕ...");

  try {
    const response = await apiRequest("/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setStatus(elements.contactStatus, response.message || "Хабарламаңыз жіберілді.", "success");
    elements.contactName.value = "";
    elements.contactPhone.value = "";
    elements.contactCar.value = "";
    elements.contactMessage.value = "";
  } catch (error) {
    setStatus(elements.contactStatus, error.message, "error");
  } finally {
    setButtonState(elements.contactSubmit, false, "ЖІБЕРУ →");
  }
}

async function submitModal() {
  const payload = {
    name: elements.modalName.value.trim(),
    phone: elements.modalPhone.value.trim(),
    car: elements.modalCar.value.trim(),
  };

  if (!payload.name || !payload.phone) {
    setStatus(elements.modalStatus, "Аты-жөніңіз бен телефон нөміріңізді толтырыңыз.", "error");
    return;
  }

  setStatus(elements.modalStatus, "", "");
  setButtonState(elements.modalSubmit, true, "ЖІБЕРІЛУДЕ...");

  try {
    const response = await apiRequest("/testdrive", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    setStatus(elements.modalStatus, response.message || "Тест-драйвке жазылдыңыз.", "success");
    elements.modalName.value = "";
    elements.modalPhone.value = "";
    elements.modalCar.value = "";
    window.setTimeout(() => {
      closeModal();
      setStatus(elements.modalStatus, "", "");
    }, 900);
  } catch (error) {
    setStatus(elements.modalStatus, error.message, "error");
  } finally {
    setButtonState(elements.modalSubmit, false, "ЖІБЕРУ →");
  }
}

function init() {
  initHero();
  initParticles();
  observeReveal();
  loadCars();

  window.addEventListener("resize", () => {
    if (window.innerWidth > 900) {
      closeNav();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeNav();
    }
  });

  elements.modal.addEventListener("click", (event) => {
    if (event.target === elements.modal) {
      closeModal();
    }
  });
}

window.filterCars = filterCars;
window.showPage = showPage;
window.toggleNav = toggleNav;
window.closeNav = closeNav;
window.openDetail = openDetail;
window.gNav = gNav;
window.gSet = gSet;
window.dTab = dTab;
window.openModal = openModal;
window.closeModal = closeModal;
window.submitForm = submitForm;
window.submitModal = submitModal;

init();
