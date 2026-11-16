// Landing: ariza formasini sahifani qayta yuklamasdan yuborish.
// fetch ishlamasa (eski brauzer, JS o'chiq) forma oddiy POST bo'lib ketadi.

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ariza");
  if (!form) return;

  const result = form.querySelector(".form-result");
  const button = form.querySelector('button[type="submit"]');

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors(form);
    result.textContent = "";
    result.className = "form-result";
    button.disabled = true;

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "fetch" },
      });
      const data = await response.json();

      if (data.ok) {
        form.reset();
        result.textContent = data.message;
        result.classList.add("ok");
      } else {
        showErrors(form, data.errors || {});
      }
    } catch (error) {
      result.textContent = form.dataset.errorText || "Xatolik yuz berdi. Qayta urinib ko'ring.";
      result.classList.add("fail");
    } finally {
      button.disabled = false;
    }
  });
});

function clearErrors(form) {
  form.querySelectorAll(".field").forEach((field) => {
    field.classList.remove("has-error");
    const box = field.querySelector(".error");
    if (box) box.textContent = "";
  });
}

// Server qaytargan xatolarni tegishli maydon ostiga chiqaramiz.
// textContent ishlatiladi — server matni HTML sifatida talqin qilinmaydi.
function showErrors(form, errors) {
  Object.entries(errors).forEach(([name, messages]) => {
    const field = form.querySelector(`[data-field="${name}"]`);
    if (!field) return;
    field.classList.add("has-error");
    field.querySelector(".error").textContent = messages.join(" ");
  });
}
