document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("analyze-form");
  const repoUrlInput = document.getElementById("repo-url");
  const statusEl = document.getElementById("status");
  const resultsContainer = document.getElementById("results-container");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const repoUrl = repoUrlInput.value.trim();
    if (!repoUrl) return;

    // Reset UI
    resultsContainer.innerHTML = "";
    resultsContainer.classList.add("hidden");
    statusEl.classList.remove("hidden");

    try {
      const resp = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      if (!resp.ok) {
        throw new Error(`Server responded with ${resp.status}`);
      }
      const respData = await resp.json();
      displayResults(respData.results, respData.report_files);
    } catch (err) {
      displayError(err);
    } finally {
      statusEl.classList.add("hidden");
    }
  });

  function displayResults(data, files = []) {
    resultsContainer.innerHTML = "";
    const summaryGrid = document.getElementById("summary-grid");
    summaryGrid.innerHTML = "";

    // ----- Build summary badges -----
    const summaryMap = {
      parser_results: {
        label: "Parser",
        ok: true,
      },
      performance_issues: {
        label: "Performance",
        ok: data.performance_issues?.count === 0,
      },
      security_findings: {
        label: "Security",
        ok: data.security_findings?.count === 0,
      },
    };

    Object.entries(summaryMap).forEach(([key, cfg]) => {
      if (!data[key]) return;
      const card = document.createElement("div");
      card.className = "summary-card";
      card.innerHTML = `
        <h3>${cfg.label}</h3>
        <span class="badge ${cfg.ok ? "badge-green" : "badge-red"}">${
        cfg.ok ? "OK" : "ISSUES"
      }</span>`;
      summaryGrid.appendChild(card);
    });

    summaryGrid.classList.remove("hidden");

    // ----- Detailed cards -----
    for (const [key, value] of Object.entries(data)) {
      const card = createResultCard(key, value);
      resultsContainer.appendChild(card);
    }

    // Download links if any
    if (files.length) {
      const downloads = document.createElement("div");
      downloads.className = "download-links";

      files.forEach((f) => {
        const ext = f.split(".").pop() ?? "";
        if (["html", "json"].includes(ext)) return; // Skip unwanted formats

        const encoded = encodeURIComponent(f);
        const btn = document.createElement("a");
        btn.href = `/download/${encoded}`;
        btn.target = "_blank";
        btn.textContent = `Download ${ext.toUpperCase()}`;
        btn.setAttribute("download", f);
        btn.className = "download-btn";
        downloads.appendChild(btn);
      });

      resultsContainer.appendChild(downloads);
    }

    // Apply highlight.js to new content
    if (window.hljs) {
      document.querySelectorAll("pre code").forEach((el) => window.hljs.highlightElement(el));
    }

    resultsContainer.classList.remove("hidden");
  }

  function createResultCard(title, content) {
    const card = document.createElement("div");
    card.className = "result-card";

    const cardTitle = document.createElement("h2");
    cardTitle.innerHTML = `${title
      .replace(/_/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase())} <span class="caret"></span>`;
    card.appendChild(cardTitle);

    const pre = document.createElement("pre");
    pre.classList.add("hidden");
    const code = document.createElement("code");
    code.className = "language-json";
    code.textContent = JSON.stringify(content, null, 2);
    pre.appendChild(code);
    card.appendChild(pre);

    // Collapse behaviour
    cardTitle.style.cursor = "pointer";
    cardTitle.addEventListener("click", () => {
      pre.classList.toggle("hidden");
      cardTitle.classList.toggle("collapsed");
    });

    return card;
  }

  function displayError(err) {
    resultsContainer.innerHTML = "";
    const card = createResultCard("Error", { message: err.message });
    resultsContainer.appendChild(card);
    resultsContainer.classList.remove("hidden");
  }
}); 