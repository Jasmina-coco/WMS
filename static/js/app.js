// Tizim sahifalari uchun kichik yordamchi skriptlar.
// Framework ishlatilmagan — faqat brauzerning o'z imkoniyatlari.

document.addEventListener("DOMContentLoaded", () => {
  setupMobileMenu();
  setupConfirmButtons();
  setupLineFormset();
  setupAutoSubmitFilters();
  setupSeriesSwitch();
});

// Telefonda chap menyuni ochish/yopish
function setupMobileMenu() {
  const toggle = document.querySelector(".menu-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (!toggle || !sidebar) return;

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    sidebar.classList.toggle("open");
  });
  document.addEventListener("click", (event) => {
    if (sidebar.classList.contains("open") && !sidebar.contains(event.target)) {
      sidebar.classList.remove("open");
    }
  });
}

// data-confirm="..." bo'lgan tugma bosilganda tasdiq so'raymiz.
// Qoldiqni o'zgartiradigan amallar tasodifan bosilib ketmasligi uchun.
function setupConfirmButtons() {
  document.querySelectorAll("[data-confirm]").forEach((button) => {
    button.addEventListener("click", (event) => {
      if (!window.confirm(button.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });
}

// Hujjat qatorlari: "Qator qo'shish" tugmasi yashirin shablondan yangi qator yasaydi.
// Django formset uchun TOTAL_FORMS sonini ham oshirib qo'yish shart.
function setupLineFormset() {
  const table = document.querySelector("[data-formset]");
  if (!table) return;

  const prefix = table.dataset.formset;
  const body = table.querySelector("tbody");
  const template = document.getElementById("empty-line");
  const totalInput = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
  const addButton = document.querySelector("[data-add-line]");

  addButton.addEventListener("click", () => {
    const index = Number(totalInput.value);
    const html = template.innerHTML.replace(/__prefix__/g, index);
    body.insertAdjacentHTML("beforeend", html);
    totalInput.value = index + 1;
    body.lastElementChild.querySelector("select, input")?.focus();
  });

  // Yangi qo'shilgan (hali saqlanmagan) qatorni shunchaki olib tashlaymiz,
  // saqlangan qatorda esa DELETE belgisini qo'yib, qatorni yashiramiz
  body.addEventListener("click", (event) => {
    const button = event.target.closest("[data-remove-line]");
    if (!button) return;
    const row = button.closest("tr");
    const deleteBox = row.querySelector('input[name$="-DELETE"]');
    const idInput = row.querySelector('input[name$="-id"]');
    if (idInput && idInput.value) {
      deleteBox.checked = true;
      row.classList.add("hidden");
    } else {
      row.querySelectorAll("select, input").forEach((el) => {
        if (el.type !== "hidden") el.value = "";
      });
      row.classList.add("hidden");
    }
  });
}

// Filtrdagi select o'zgarsa, forma o'zi yuboriladi
function setupAutoSubmitFilters() {
  document.querySelectorAll(".filters select").forEach((select) => {
    select.addEventListener("change", () => select.form.submit());
  });
}

// Bosh sahifadagi "Kirim / Chiqim" almashtirgichi: grafikda qaysi qatorlar ko'rinishini tanlaydi
function setupSeriesSwitch() {
  const switcher = document.querySelector("[data-switch]");
  if (!switcher) return;
  const card = switcher.closest(".card");

  switcher.addEventListener("click", (event) => {
    const button = event.target.closest("[data-show]");
    if (!button) return;
    switcher.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === button));
    card.querySelectorAll("[data-series]").forEach((el) => {
      el.classList.toggle("shown", el.dataset.series === button.dataset.show);
    });
  });
}
