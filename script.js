

function renderMarkdown(text) {
    if (!text) return "No response available.";

    // Escape HTML for safety
    let content = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Inline formatting
    content = content
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>");

    const lines = content.split("\n");
    let html = "";
    let inList = false;
    let listType = "";

    for (const line of lines) {
        const trimmed = line.trim();

        if (!trimmed) {
            if (inList) {
                html += listType === "ol" ? "</ol>" : "</ul>";
                inList = false;
            }
            continue;
        }

        const heading = trimmed.match(/^(#{1,6})\s+(.*)$/);
        const bullet = trimmed.match(/^[-*]\s+(.*)$/);
        const numbered = trimmed.match(/^\d+\.\s+(.*)$/);

        if (heading) {
            if (inList) {
                html += listType === "ol" ? "</ol>" : "</ul>";
                inList = false;
            }
            const level = heading[1].length;
            html += `<h${level}>${heading[2]}</h${level}>`;
        } else if (bullet || numbered) {
            const type = numbered ? "ol" : "ul";

            if (!inList || listType !== type) {
                if (inList) html += listType === "ol" ? "</ol>" : "</ul>";
                html += type === "ol" ? "<ol>" : "<ul>";
                listType = type;
                inList = true;
            }

            html += `<li>${(bullet || numbered)[1]}</li>`;
        } else {
            if (inList) {
                html += listType === "ol" ? "</ol>" : "</ul>";
                inList = false;
            }
            html += `<p>${trimmed}</p>`;
        }
    }

    if (inList) html += listType === "ol" ? "</ol>" : "</ul>";

    return html;
}



document.addEventListener("DOMContentLoaded", () => {
    const navButtons = document.querySelectorAll(".nav-item");
    const pages = document.querySelectorAll(".page");
    const pageTitle = document.getElementById("page-title");

    const pageNames = {
        dashboard: "Dashboard",
        playground: "Experiment Playground",
        analysis: "Agent Analysis",
        compare: "Compare Experiments",
        results: "Performance & Results"
    };



    // Navigate between pages
    function navigateTo(pageName) {
        const targetPage = document.getElementById(pageName);

        if (!targetPage) return;

        // Hide all pages
        pages.forEach(page => {
            page.classList.remove("active");
        });

        // Show selected page
        targetPage.classList.add("active");

        // Update sidebar active state
        navButtons.forEach(button => {
            button.classList.toggle(
                "active",
                button.dataset.page === pageName
            );
        });

        // Update topbar title
        pageTitle.textContent = pageNames[pageName] || "Dashboard";

        // Scroll to top
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }

    // Sidebar navigation
    navButtons.forEach(button => {
        button.addEventListener("click", () => {
            navigateTo(button.dataset.page);
        });
    });

    // Buttons that navigate to another page
    document.querySelectorAll("[data-navigate]").forEach(button => {
        button.addEventListener("click", () => {
            const destination = button.dataset.navigate;
            navigateTo(destination);
        });
    });

    // Configuration selection
    document.querySelectorAll("[data-config]").forEach(button => {
        button.addEventListener("click", () => {
            const selectedConfig = button.dataset.config;

            // Keep the selected configuration for the Playground
            window.selectedConfiguration = selectedConfig;

            navigateTo("playground");

            console.log(
                "Selected experiment configuration:",
                selectedConfig
            );
        });
    });

    // Default selected configuration
    window.selectedConfiguration = "A";

    console.log("Debate AI interface initialized.");
});


document.addEventListener("DOMContentLoaded", () => {

    const navItems = document.querySelectorAll(".nav-item");
    const pages = document.querySelectorAll(".page");
    const pageTitle = document.getElementById("page-title");

    const pageNames = {
        dashboard: "Dashboard",
        playground: "Experiment Playground",
        analysis: "Agent Analysis",
        compare: "Compare Experiments",
        results: "Performance & Results"
    };

    function showPage(pageId) {
        // Hide all pages
        pages.forEach(page => {
            page.classList.remove("active");
        });

        // Remove active state from navigation
        navItems.forEach(item => {
            item.classList.remove("active");
        });

        // Show selected page
        const selectedPage = document.getElementById(pageId);

        if (selectedPage) {
            selectedPage.classList.add("active");
        }

        // Highlight selected navigation
        const selectedNav = document.querySelector(
            `.nav-item[data-page="${pageId}"]`
        );

        if (selectedNav) {
            selectedNav.classList.add("active");
        }

        // Update page title
        if (pageTitle && pageNames[pageId]) {
            pageTitle.textContent = pageNames[pageId];
        }
    }

    // Sidebar navigation
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const pageId = item.dataset.page;
            showPage(pageId);
        });
    });

    // Buttons that navigate to another page
    document.querySelectorAll("[data-navigate]").forEach(button => {
        button.addEventListener("click", () => {
            const pageId = button.dataset.navigate;
            showPage(pageId);
        });
    });

    // Configuration cards
    document.querySelectorAll("[data-config]").forEach(button => {
        button.addEventListener("click", () => {
            const config = button.dataset.config;

            showPage("playground");

            // Store selected configuration temporarily
            sessionStorage.setItem("selectedConfig", config);

            console.log("Selected configuration:", config);
        });
    });

});


/* ==========================================
   PLAYGROUND CONFIGURATION SELECTION
========================================== */

document.addEventListener("DOMContentLoaded", function () {
    const configButtons = document.querySelectorAll("[data-play-config]");
    const configInfo = document.getElementById("selected-config-info");
    const expectedCalls = document.getElementById("expected-calls");

    const configDetails = {
        A: {
            title: "Configuration A — Direct Answer",
            description: "One model call. The model responds directly to your question.",
            calls: "1 model call"
        },
        B: {
            title: "Configuration B — Reasoning Prompt",
            description: "One model call using a reasoning-guided prompt.",
            calls: "1 model call"
        },
        C: {
            title: "Configuration C — Two-Agent Debate",
            description: "Solver → Critic → Revision. Three model calls.",
            calls: "3 model calls"
        },
        D: {
            title: "Configuration D — Solver–Critic–Judge",
            description: "Solver → Critic → Revision → Judge. Four model calls.",
            calls: "4 model calls"
        }
    };

    function selectConfig(config) {
        const details = configDetails[config];
        if (!details) return;

        window.selectedConfiguration = config;

        configButtons.forEach(button => {
            button.classList.toggle(
                "selected",
                button.dataset.playConfig === config
            );
        });

        if (configInfo) {
            configInfo.innerHTML = `
                <strong>${details.title}</strong><br>
                ${details.description}
            `;
        }

        if (expectedCalls) {
            expectedCalls.textContent = details.calls;
        }

        sessionStorage.setItem("selectedPlayConfig", config);
    }

    configButtons.forEach(button => {
        button.addEventListener("click", function () {
            selectConfig(this.dataset.playConfig);
        });
    });

    const savedConfig = sessionStorage.getItem("selectedPlayConfig") || "A";
    selectConfig(savedConfig);
});

/* ==========================================
   PLAYGROUND — REAL BACKEND INTEGRATION
========================================== */

document.addEventListener("DOMContentLoaded", () => {
    const runButton = document.getElementById("run-experiment-btn");
    const questionInput = document.getElementById("question-input");

    const outputPlaceholder = document.getElementById("output-placeholder");
    const experimentOutput = document.getElementById("experiment-output");
    const outputStatus = document.getElementById("output-status");

    const finalAnswer = document.getElementById("final-answer");
    const stageContainer = document.getElementById("stage-output-container");

    const configResult = document.getElementById("result-config");
    const runtimeResult = document.getElementById("result-runtime");

    if (!runButton) return;

    runButton.addEventListener("click", async () => {

        const question = questionInput.value.trim();

        const configuration =
            window.selectedConfiguration ||
            sessionStorage.getItem("selectedPlayConfig") ||
            sessionStorage.getItem("selectedConfig") ||
            "A";

        // Validate question
        if (!question) {
            alert("Please enter a question first.");
            questionInput.focus();
            return;
        }

        // Prepare UI
        runButton.disabled = true;
        runButton.innerHTML = "⏳ Running Experiment...";

        outputStatus.textContent = "RUNNING";
        outputStatus.classList.add("running");

        outputPlaceholder.classList.remove("hidden");
        experimentOutput.classList.add("hidden");

        outputPlaceholder.innerHTML = `
            <div class="output-placeholder-icon">⏳</div>
            <h3>Experiment is running</h3>
            <p>Waiting for Qwen 2.5:3B to complete the selected configuration...</p>
        `;

        try {

            // Send question to FastAPI backend
            const response = await fetch("http://127.0.0.1:8000/run", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    question: question,
                    configuration: configuration
                })
            });

            const data = await response.json();

            // Handle API errors
            if (!response.ok) {
                const errorMessage =
                    typeof data.detail === "string"
                        ? data.detail
                        : data.detail?.error || JSON.stringify(data.detail);

                throw new Error(errorMessage || "Experiment failed.");
            }

            // Display final output
            outputPlaceholder.classList.add("hidden");
            experimentOutput.classList.remove("hidden");

            outputStatus.textContent = "COMPLETED";
            outputStatus.classList.remove("running");

            configResult.textContent =
                `${data.configuration} — ${data.configuration_name}`;

            runtimeResult.textContent =
                `${data.execution_time} sec`;

            finalAnswer.innerHTML = renderMarkdown(
            data.final_answer || "No final response received."
            );

            // Clear previous stage outputs
            stageContainer.innerHTML = "";

            // Display agent stages
            if (data.stages && Object.keys(data.stages).length > 0) {

                
Object.entries(data.stages).forEach(([stageName, stage]) => {

    const stageCard = document.createElement("div");
    stageCard.className = "agent-output";

    const heading = document.createElement("h3");
    heading.textContent = stageName
        .replace(/_/g, " ")
        .replace(/\b\w/g, char => char.toUpperCase());

    const responseText = document.createElement("div");
    responseText.className = "agent-response";

    const agentResponse = stage.response || "No response available.";
   

    responseText.innerHTML = renderMarkdown(agentResponse);

    const details = document.createElement("small");
    details.textContent =
        `Time: ${stage.time_seconds ?? 0}s | Generated tokens: ${stage.generated_tokens ?? 0}`;

    stageCard.appendChild(heading);
    stageCard.appendChild(responseText);
    stageCard.appendChild(details);

    stageContainer.appendChild(stageCard);
});

            }

            console.log("Experiment completed:", data);

        } catch (error) {

            outputStatus.textContent = "ERROR";
            outputStatus.classList.remove("running");

            outputPlaceholder.classList.remove("hidden");
            experimentOutput.classList.add("hidden");

            outputPlaceholder.innerHTML = `
                <div class="output-placeholder-icon">⚠️</div>
                <h3>Experiment Failed</h3>
                <p></p>
            `;

            outputPlaceholder.querySelector("p").textContent = error.message;

            console.error("Experiment error:", error);

        } finally {

            // Restore button
            runButton.disabled = false;
            runButton.innerHTML = "<span>▶</span> Run Experiment";
        }
    });
});


/* =========================================================
   FINAL EXPERIMENT RESULTS DASHBOARD
========================================================= */

(() => {
    const RESULTS_API = "http://127.0.0.1:8000/results";

    let resultsSummary = null;
    let resultsRows = [];
    let resultsCharts = {};

    const configOrder = ["A", "B", "C", "D"];

    function safeText(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function getConfig(config) {
        return resultsSummary?.configurations?.[config] || {};
    }

    function destroyChart(id) {
        if (resultsCharts[id]) {
            resultsCharts[id].destroy();
            delete resultsCharts[id];
        }
    }

    function createChart(id, type, data, options = {}) {
        const canvas = document.getElementById(id);

        if (!canvas || typeof Chart === "undefined") {
            return;
        }

        destroyChart(id);

        resultsCharts[id] = new Chart(canvas, {
            type,
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 700
                },
                plugins: {
                    legend: {
                        labels: {
                            color: "#aab4c8"
                        }
                    }
                },
                scales: type !== "doughnut" ? {
                    x: {
                        ticks: { color: "#9ca8bd" },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: "#9ca8bd" },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    }
                } : {},
                ...options
            }
        });
    }

    function renderSummary() {
        configOrder.forEach(config => {
            const data = getConfig(config);
            const element = document.getElementById(`accuracy-${config.toLowerCase()}`);

            if (element) {
                element.textContent = `${Number(data.final_accuracy || 0).toFixed(2)}%`;
            }
        });

        const bestConfig = configOrder.reduce((best, current) => {
            return getConfig(current).final_accuracy >
                getConfig(best).final_accuracy ? current : best;
        }, configOrder[0]);

        const best = getConfig(bestConfig);

        const bestName = document.getElementById("best-config-name");
        const bestAccuracy = document.getElementById("best-config-accuracy");
        const bestDescription = document.getElementById("best-config-description");

        if (bestName) {
            bestName.textContent = `${best.name || `Configuration ${bestConfig}`} — Best Performing`;
        }

        if (bestAccuracy) {
            bestAccuracy.textContent = `${Number(best.final_accuracy || 0).toFixed(2)}%`;
        }

        if (bestDescription) {
            bestDescription.textContent =
                `${best.final_correct || 0} correct out of ${best.total_questions || 0} questions. ` +
                `Average execution time: ${Number(best.average_time || 0).toFixed(2)} seconds per question.`;
        }
    }

    function renderCharts() {
        const initialAccuracy = configOrder.map(
            c => Number(getConfig(c).initial_accuracy || 0)
        );

        const finalAccuracy = configOrder.map(
            c => Number(getConfig(c).final_accuracy || 0)
        );

        const runtimes = configOrder.map(
            c => Number(getConfig(c).average_time || 0)
        );

        const calls = configOrder.map(
            c => Number(getConfig(c).average_model_calls || 0)
        );

        const correct = configOrder.map(
            c => Number(getConfig(c).final_correct || 0)
        );

        const total = configOrder.map(
            c => Number(getConfig(c).total_questions || 0)
        );

        const incorrect = configOrder.map(
            (c, i) => Math.max(0, total[i] - correct[i])
        );

        createChart("accuracy-chart", "bar", {
            labels: configOrder,
            datasets: [
                {
                    label: "Initial Accuracy (%)",
                    data: initialAccuracy,
                    backgroundColor: "#64748b",
                    borderRadius: 6
                },
                {
                    label: "Final Accuracy (%)",
                    data: finalAccuracy,
                    backgroundColor: "#8b5cf6",
                    borderRadius: 6
                }
            ]
        }, {
            scales: {
                x: {
                    ticks: { color: "#9ca8bd" },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: "#9ca8bd",
                        callback: value => `${value}%`
                    },
                    grid: { color: "rgba(255,255,255,0.05)" }
                }
            }
        });

        createChart("runtime-chart", "bar", {
            labels: configOrder,
            datasets: [{
                label: "Average Seconds",
                data: runtimes,
                backgroundColor: ["#60a5fa", "#a78bfa", "#34d399", "#fb923c"],
                borderRadius: 7
            }]
        });

        createChart("calls-chart", "bar", {
            labels: configOrder,
            datasets: [{
                label: "Average Model Calls",
                data: calls,
                backgroundColor: ["#60a5fa", "#a78bfa", "#34d399", "#fb923c"],
                borderRadius: 7
            }]
        });

        createChart("correctness-chart", "bar", {
            labels: configOrder,
            datasets: [
                {
                    label: "Correct",
                    data: correct,
                    backgroundColor: "#34d399",
                    borderRadius: 5
                },
                {
                    label: "Incorrect",
                    data: incorrect,
                    backgroundColor: "#fb7185",
                    borderRadius: 5
                }
            ]
        }, {
            scales: {
                x: {
                    stacked: true,
                    ticks: { color: "#9ca8bd" },
                    grid: { display: false }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    ticks: { color: "#9ca8bd" },
                    grid: { color: "rgba(255,255,255,0.05)" }
                }
            }
        });
    }

    function renderTable() {
        const tbody = document.getElementById("results-table-body");
        const filter = document.getElementById("results-config-filter");
        const countElement = document.getElementById("results-table-count");

        if (!tbody) return;

        const selected = filter?.value || "ALL";

        const filtered = resultsRows.filter(row =>
            selected === "ALL" || row.configuration === selected
        );

        if (countElement) {
            countElement.textContent =
                `${filtered.length} records displayed / ${resultsRows.length} total`;
        }

        if (!filtered.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9">No records found.</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = filtered.map(row => {
            const config = safeText(row.configuration);
            const correctClass = row.final_correct ? "correct" : "incorrect";
            const initialClass = row.initial_correct ? "correct" : "incorrect";

            return `
                <tr>
                    <td title="${safeText(row.question_id)}">
                        ${safeText(row.question_id)}
                    </td>

                    <td>
                        <span class="config-badge config-${config.toLowerCase()}">
                            ${config}
                        </span>
                    </td>

                    <td title="${safeText(row.initial_prediction)}">
                        ${safeText(row.initial_prediction)}
                    </td>

                    <td title="${safeText(row.final_prediction)}">
                        ${safeText(row.final_prediction)}
                    </td>

                    <td title="${safeText(row.reference_answer)}">
                        ${safeText(row.reference_answer)}
                    </td>

                    <td>
                        <span class="result-badge ${initialClass}">
                            ${row.initial_correct ? "Correct" : "Wrong"}
                        </span>
                    </td>

                    <td>
                        <span class="result-badge ${correctClass}">
                            ${row.final_correct ? "Correct" : "Wrong"}
                        </span>
                    </td>

                    <td>${Number(row.model_calls || 0)}</td>

                    <td>${Number(row.time_seconds || 0).toFixed(2)}</td>
                </tr>
            `;
        }).join("");
    }

    async function loadResults() {
        const loading = document.getElementById("results-loading");
        const error = document.getElementById("results-error");

        if (loading) {
            loading.classList.remove("hidden");
            loading.textContent = "Loading experimental results...";
        }

        if (error) {
            error.classList.add("hidden");
        }

        try {
            const [summaryResponse, dataResponse] = await Promise.all([
                fetch(`${RESULTS_API}/summary`),
                fetch(`${RESULTS_API}/data`)
            ]);

            if (!summaryResponse.ok || !dataResponse.ok) {
                throw new Error("Backend API returned an error.");
            }

            const summary = await summaryResponse.json();
            const data = await dataResponse.json();

            if (!summary.success || !data.success) {
                throw new Error("Unable to load experiment data.");
            }

            resultsSummary = summary;
            resultsRows = data.data || [];

            renderSummary();
            renderCharts();
            renderTable();

            if (loading) {
                loading.classList.add("hidden");
            }

            console.log("DebateAI results loaded successfully.", summary);

        } catch (err) {
            console.error("Results loading error:", err);

            if (loading) {
                loading.classList.add("hidden");
            }

            if (error) {
                error.textContent =
                    "Unable to load results. Ensure the backend is running on port 8000.";
                error.classList.remove("hidden");
            }
        }
    }

    // Refresh button
    document.getElementById("refresh-results-btn")
        ?.addEventListener("click", loadResults);

    // Table filter
    document.getElementById("results-config-filter")
        ?.addEventListener("change", renderTable);

    // Load results when Results page is opened
    document.querySelectorAll('[data-page="results"]').forEach(button => {
        button.addEventListener("click", () => {
            loadResults();
        });
    });

    // Initial load in case Results page is already active
    loadResults();

})();


/* =========================================================
   COMPARE EXPERIMENTS DASHBOARD
========================================================= */

(() => {
    const API = "http://127.0.0.1:8000/results";

    let compareSummary = null;
    let compareRows = [];
    let compareCharts = {};

    const configs = ["A", "B", "C", "D"];

    function compareDestroyChart(id) {
        if (compareCharts[id]) {
            compareCharts[id].destroy();
            delete compareCharts[id];
        }
    }

    function compareCreateChart(id, type, data, options = {}) {
        const canvas = document.getElementById(id);

        if (!canvas || typeof Chart === "undefined") return;

        compareDestroyChart(id);

        compareCharts[id] = new Chart(canvas, {
            type,
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 500 },
                plugins: {
                    legend: {
                        labels: { color: "#aab4c8" }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: "#9ca8bd" },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: "#9ca8bd" },
                        grid: { color: "rgba(255,255,255,0.05)" }
                    }
                },
                ...options
            }
        });
    }

    function compareGetConfig(config) {
        return compareSummary?.configurations?.[config] || {};
    }

    function compareRenderCards() {
        configs.forEach(config => {
            const data = compareGetConfig(config);
            const suffix = config.toLowerCase();

            const accuracy = document.getElementById(`compare-accuracy-${suffix}`);
            const correct = document.getElementById(`compare-correct-${suffix}`);
            const runtime = document.getElementById(`compare-time-${suffix}`);
            const calls = document.getElementById(`compare-calls-${suffix}`);

            if (accuracy) {
                accuracy.textContent =
                    `${Number(data.final_accuracy || 0).toFixed(2)}%`;
            }

            if (correct) {
                correct.textContent =
                    `${data.final_correct || 0}/${data.total_questions || 0}`;
            }

            if (runtime) {
                runtime.textContent =
                    `${Number(data.average_time || 0).toFixed(2)} s`;
            }

            if (calls) {
                calls.textContent =
                    Number(data.average_model_calls || 0).toFixed(2);
            }
        });
    }

    function compareRenderCharts() {
        const accuracy = configs.map(c =>
            Number(compareGetConfig(c).final_accuracy || 0)
        );

        const runtime = configs.map(c =>
            Number(compareGetConfig(c).average_time || 0)
        );

        compareCreateChart("compare-accuracy-chart", "bar", {
            labels: configs.map(c => `Configuration ${c}`),
            datasets: [{
                label: "Final Accuracy (%)",
                data: accuracy,
                backgroundColor: [
                    "#60a5fa",
                    "#a78bfa",
                    "#34d399",
                    "#fb923c"
                ],
                borderRadius: 7
            }]
        }, {
            scales: {
                x: {
                    ticks: { color: "#9ca8bd" },
                    grid: { display: false }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        color: "#9ca8bd",
                        callback: value => `${value}%`
                    },
                    grid: { color: "rgba(255,255,255,0.05)" }
                }
            }
        });

        compareCreateChart("compare-runtime-chart", "bar", {
            labels: configs.map(c => `Configuration ${c}`),
            datasets: [{
                label: "Average Execution Time (seconds)",
                data: runtime,
                backgroundColor: [
                    "#60a5fa",
                    "#a78bfa",
                    "#34d399",
                    "#fb923c"
                ],
                borderRadius: 7
            }]
        });
    }

    function compareEscape(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function compareRenderQuestionOptions() {
        const select = document.getElementById("compare-question-select");
        if (!select) return;

        const questionIds = [...new Set(
            compareRows.map(row => row.question_id).filter(Boolean)
        )].sort();

        select.innerHTML = "";

        if (!questionIds.length) {
            select.innerHTML = `<option value="">No questions available</option>`;
            return;
        }

        select.innerHTML = `
            <option value="">Choose a question...</option>
            ${questionIds.map(id =>
                `<option value="${compareEscape(id)}">${compareEscape(id)}</option>`
            ).join("")}
        `;
    }

    function compareRenderQuestion(questionId) {
        const tbody = document.getElementById("compare-question-table-body");
        const details = document.getElementById("compare-question-details");

        if (!tbody) return;

        if (!questionId) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8">Select a question above.</td>
                </tr>
            `;

            if (details) {
                details.textContent =
                    "Select a question to compare all four configurations.";
            }

            return;
        }

        const rows = compareRows.filter(row =>
            String(row.question_id) === String(questionId)
        );

        rows.sort((a, b) =>
            configs.indexOf(a.configuration) - configs.indexOf(b.configuration)
        );

        if (details) {
            details.innerHTML = `
                <strong>Question ID:</strong> ${compareEscape(questionId)}
                <br>
                <strong>Configurations found:</strong> ${rows.length} / 4
                <br>
                <strong>Reference Answer:</strong>
                ${compareEscape(rows[0]?.reference_answer ?? "N/A")}
            `;
        }

        if (!rows.length) {
            tbody.innerHTML = `
                <tr><td colspan="8">No records found.</td></tr>
            `;
            return;
        }

        tbody.innerHTML = rows.map(row => {
            const initialClass = row.initial_correct ? "correct" : "incorrect";
            const finalClass = row.final_correct ? "correct" : "incorrect";

            return `
                <tr>
                    <td><strong>Configuration ${compareEscape(row.configuration)}</strong></td>
                    <td title="${compareEscape(row.initial_prediction)}">
                        ${compareEscape(row.initial_prediction)}
                    </td>
                    <td title="${compareEscape(row.final_prediction)}">
                        ${compareEscape(row.final_prediction)}
                    </td>
                    <td>${compareEscape(row.reference_answer)}</td>
                    <td>
                        <span class="result-badge ${initialClass}">
                            ${row.initial_correct ? "Correct" : "Wrong"}
                        </span>
                    </td>
                    <td>
                        <span class="result-badge ${finalClass}">
                            ${row.final_correct ? "Correct" : "Wrong"}
                        </span>
                    </td>
                    <td>${Number(row.model_calls || 0)}</td>
                    <td>${Number(row.time_seconds || 0).toFixed(2)}</td>
                </tr>
            `;
        }).join("");
    }

    async function compareLoadData() {
        const button = document.getElementById("refresh-compare-btn");

        if (button) {
            button.disabled = true;
            button.textContent = "Loading...";
        }

        try {
            const [summaryResponse, dataResponse] = await Promise.all([
                fetch(`${API}/summary`),
                fetch(`${API}/data`)
            ]);

            if (!summaryResponse.ok || !dataResponse.ok) {
                throw new Error("Failed to retrieve comparison data.");
            }

            const summary = await summaryResponse.json();
            const data = await dataResponse.json();

            if (!summary.success || !data.success) {
                throw new Error("Backend returned unsuccessful data.");
            }

            compareSummary = summary;
            compareRows = data.data || [];

            compareRenderCards();
            compareRenderCharts();
            compareRenderQuestionOptions();

            const select = document.getElementById("compare-question-select");
            if (select && select.value) {
                compareRenderQuestion(select.value);
            } else {
                compareRenderQuestion("");
            }

            console.log("Compare Experiments loaded successfully.");

        } catch (error) {
            console.error("Compare Experiments loading error:", error);

            const details = document.getElementById("compare-question-details");

            if (details) {
                details.textContent =
                    "Unable to load data. Please ensure the backend is running on port 8000.";
            }

        } finally {
            if (button) {
                button.disabled = false;
                button.textContent = "↻ Refresh Comparison";
            }
        }
    }

    document.getElementById("refresh-compare-btn")
        ?.addEventListener("click", compareLoadData);

    document.getElementById("compare-question-select")
        ?.addEventListener("change", event => {
            compareRenderQuestion(event.target.value);
        });

    document.querySelectorAll('[data-page="compare"]').forEach(button => {
        button.addEventListener("click", compareLoadData);
    });

    compareLoadData();

})();
