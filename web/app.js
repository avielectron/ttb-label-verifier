// app.js
// Talks to the FastAPI backend for single-label and batch verification.
// No external calls — everything hits this app's own /api endpoints.

let lastBrandResult = null;

const singleForm = document.getElementById("single-form");
const resultsBox = document.getElementById("single-results");
const timingEl = document.getElementById("timing");
const brandRow = document.getElementById("brand-result");
const abvRow = document.getElementById("abv-result");
const warningRow = document.getElementById("warning-result");

function statusSpan(status) {
  return `<span class="status-${status}">${status}</span>`;
}

function renderBrandRow(brandResult) {
  lastBrandResult = brandResult;
  const overrideButton = brandResult.status !== "PASS"
    ? `<button type="button" class="override-button" id="override-brand-btn">Agent Override: Mark PASS</button>`
    : "";

  brandRow.innerHTML = `
    <span>Brand Name (score: ${brandResult.score})</span>
    <span>${statusSpan(brandResult.status)} ${overrideButton}</span>
  `;

  const overrideBtn = document.getElementById("override-brand-btn");
  if (overrideBtn) {
    overrideBtn.addEventListener("click", () => {
      lastBrandResult.status = "PASS";
      lastBrandResult.overridden_by_agent = true;
      renderBrandRow(lastBrandResult);
    });
  }
}

function renderAbvRow(abvResult) {
  const found = abvResult.found !== null && abvResult.found !== undefined
    ? `${abvResult.found}%`
    : "not found";
  abvRow.innerHTML = `
    <span>ABV (expected ${abvResult.expected}%, found ${found})</span>
    <span>${statusSpan(abvResult.status)}</span>
  `;
}

function renderWarningRow(warningResult) {
  warningRow.innerHTML = `
    <span>Government Warning — ${warningResult.reason || ""}</span>
    <span>${statusSpan(warningResult.status)}</span>
  `;
}

singleForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = singleForm.querySelector("button[type=submit]");
  submitButton.disabled = true;
  submitButton.textContent = "Verifying...";

  try {
    const formData = new FormData(singleForm);
    const response = await fetch("/api/verify", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || "Verification failed.");
    }

    const data = await response.json();

    timingEl.textContent = `(${data.ocr_seconds}s)`;
    renderBrandRow(data.brand);
    renderAbvRow(data.abv);
    renderWarningRow(data.government_warning);
    resultsBox.hidden = false;
  } catch (err) {
    alert(err.message);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Verify Label";
  }
});

const batchForm = document.getElementById("batch-form");
const batchStatus = document.getElementById("batch-status");

batchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = batchForm.querySelector("button[type=submit]");
  submitButton.disabled = true;
  submitButton.textContent = "Processing batch...";
  batchStatus.textContent = "";

  try {
    const formData = new FormData(batchForm);
    const response = await fetch("/api/batch", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || "Batch processing failed.");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "batch_results.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    batchStatus.textContent = "Batch complete. Results downloaded.";
  } catch (err) {
    batchStatus.textContent = `Error: ${err.message}`;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Run Batch & Download Results";
  }
});
