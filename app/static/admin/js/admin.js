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

function renderCarCard(car) {
  return `
    <article class="admin-car-card">
      <img src="${escapeHtml(car.image_url)}" alt="${escapeHtml(car.name)}" loading="lazy">
      <div class="admin-car-body">
        <div class="admin-car-top">
          <h3>${escapeHtml(car.name)}</h3>
          <span>${escapeHtml(car.price_display)} ₸</span>
        </div>
        <p>${escapeHtml(car.description)}</p>
        <a href="${escapeHtml(car.image_url)}" target="_blank" rel="noreferrer">Cloudinary URL ашу</a>
      </div>
    </article>`;
}

function setResult(container, message, type = "") {
  container.className = `upload-result ${type}`.trim();
  container.innerHTML = message;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("carUploadForm");
  if (!form) {
    return;
  }

  const imageInput = document.getElementById("imageInput");
  const selectedFile = document.getElementById("selectedFile");
  const previewCard = document.getElementById("previewCard");
  const previewImage = document.getElementById("previewImage");
  const submitButton = document.getElementById("submitButton");
  const uploadResult = document.getElementById("uploadResult");
  const carGrid = document.getElementById("carGrid");
  const emptyState = document.getElementById("emptyState");

  imageInput.addEventListener("change", () => {
    const file = imageInput.files?.[0];
    if (!file) {
      selectedFile.textContent = "Файл әлі таңдалған жоқ";
      previewImage.hidden = true;
      previewImage.removeAttribute("src");
      return;
    }

    selectedFile.textContent = `${file.name} • ${(file.size / 1024 / 1024).toFixed(2)} MB`;
    const reader = new FileReader();
    reader.onload = (event) => {
      previewImage.src = event.target?.result || "";
      previewImage.hidden = false;
    };
    reader.readAsDataURL(file);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    submitButton.disabled = true;
    submitButton.textContent = "Жүктеліп жатыр...";
    setResult(uploadResult, "");

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
        },
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || "Жүктеу кезінде қате шықты");
      }

      setResult(
        uploadResult,
        `Сақталды. secure_url: <a href="${escapeHtml(payload.secure_url)}" target="_blank" rel="noreferrer">${escapeHtml(payload.secure_url)}</a>`,
        "success"
      );

      if (emptyState) {
        emptyState.remove();
      }
      carGrid.insertAdjacentHTML("afterbegin", renderCarCard(payload.car));

      form.reset();
      selectedFile.textContent = "Файл әлі таңдалған жоқ";
      previewImage.hidden = true;
      previewImage.removeAttribute("src");
      previewCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (error) {
      setResult(uploadResult, escapeHtml(error.message), "error");
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Фото мен мәліметті сақтау";
    }
  });
});
