"""Static UI styles and browser behavior, separate from Python event wiring."""

APP_CSS = """
:root, body, .gradio-container {
    --font: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    font-family: var(--font) !important;
}
.gradio-container {
    width: 100% !important;
    max-width: 1440px !important;
    min-width: 0 !important;
    margin-inline: auto !important;
}
:root .gradio-container > .main.fillable {
    padding-left: clamp(.75rem, 3vw, 2rem) !important;
    padding-right: clamp(.75rem, 3vw, 2rem) !important;
}
.gradio-container main,
.gradio-container .main,
.gradio-container .column,
.gradio-container .row,
.gradio-container [role="tabpanel"] { min-width: 0 !important; }
.gradio-container [role="tablist"] {
    max-width: 100%;
    overflow-x: auto !important;
    overflow-y: hidden;
    scrollbar-width: thin;
}
#asmr-dubber-product-marker { margin: .25rem 0 1rem; }
#asmr-dubber-product-marker h1 { margin: 0; font-size: clamp(1.75rem, 5vw, 2.45rem); }
#asmr-dubber-product-marker p { margin: .35rem 0 0; color: var(--body-text-color-subdued); }
#workflow-hint { border-left: 4px solid var(--color-accent); padding-left: .85rem; }
#workflow-hint #workflow-hint { border-left: 0 !important; padding-left: 0 !important; }
#project-start {
    border: 1px solid var(--border-color-primary) !important;
    border-left: 4px solid var(--color-accent) !important;
    border-radius: 10px !important;
    padding: clamp(.75rem, 2vw, 1.15rem) !important;
}
#project-start #project-start {
    border: 0 !important;
    padding: 0 !important;
}
#project-summary {
    margin: .25rem 0 .75rem !important;
    padding: .7rem .85rem !important;
    border-radius: 8px;
    background: var(--block-background-fill);
    color: var(--body-text-color-subdued);
}
#project-summary p { margin: 0 !important; }
#project-summary #project-summary {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
}
.workflow-actions button { min-height: 44px; font-weight: 600; }
#project-status {
    border-left: 4px solid var(--color-accent) !important;
    padding: .65rem .85rem !important;
    background: var(--block-background-fill);
}
#project-status p { margin: 0 !important; white-space: pre-wrap; }
#project-status #project-status { border-left: 0 !important; padding: 0 !important; }
#autoflow-start {
    border: 1px solid var(--border-color-primary) !important;
    border-left: 4px solid var(--color-accent) !important;
    border-radius: 10px !important;
    padding: clamp(.75rem, 2vw, 1.15rem) !important;
}
#autoflow-start #autoflow-start {
    border: 0 !important;
    padding: 0 !important;
}
#autoflow-status {
    border-left: 4px solid var(--color-accent) !important;
    padding: .65rem .85rem !important;
}
#autoflow-options {
    border: 1px solid var(--border-color-primary) !important;
    border-radius: 10px !important;
    padding: clamp(.75rem, 2vw, 1.15rem) !important;
    margin-top: .75rem !important;
}
#autoflow-options #autoflow-options {
    border: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}
#autoflow-options-note,
#autoflow-settings-note {
    border-left: 4px solid var(--color-accent) !important;
    padding: .65rem .85rem !important;
    background: var(--block-background-fill);
    border-radius: 6px;
}
#autoflow-options-note p,
#autoflow-settings-note p { margin: 0 !important; }
#autoflow-options-note #autoflow-options-note,
#autoflow-settings-note #autoflow-settings-note {
    border-left: 0 !important;
    padding: 0 !important;
    background: transparent !important;
}
.autoflow-section-title { margin-top: .35rem !important; }
.autoflow-table table { min-width: 720px; }
.status-panel textarea, .diagnostics-panel textarea { font-family: var(--font); }
.optional-section { opacity: .96; }
.sentence-table, .backend-table, .profile-table {
    min-width: 0 !important;
    max-width: 100% !important;
    overflow-x: auto !important;
}
.sentence-table table { min-width: 760px; }
.backend-table table { min-width: 900px; }
.profile-table table { min-width: 640px; }
.gradio-container code { overflow-wrap: anywhere; }
button:focus-visible, input:focus-visible, textarea:focus-visible, [role="tab"]:focus-visible {
    outline: 3px solid var(--color-accent) !important;
    outline-offset: 2px;
}
footer { display: none !important; }
@media (max-width: 640px) {
    .mobile-stack { flex-direction: column !important; }
    .mobile-stack > * { width: 100% !important; min-width: 0 !important; }
}
"""

_NATIVE_OUTPUT_AUDIO_JS = """
() => {
    const syncOutputAudio = () => {
        for (const id of ["output-audio-preview", "output-stem-preview"]) {
            const root = document.getElementById(id);
            const audio = root?.querySelector("audio");
            const download = root?.querySelector('a[data-testid="download-link"]');
            if (audio && download && audio.src !== download.href) {
                audio.src = download.href;
                audio.load();
            }
        }
    };
    globalThis.__asmrDubberAudioObserver?.disconnect();
    const observer = new MutationObserver(syncOutputAudio);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["href"],
    });
    globalThis.__asmrDubberAudioObserver = observer;
    syncOutputAudio();

    clearInterval(globalThis.__asmrDubberAutoflowLogTimer);
    let previousLog = null;
    globalThis.__asmrDubberAutoflowLogTimer = setInterval(() => {
        const textarea = document.querySelector("#autoflow-run-log textarea");
        if (!textarea || textarea.value === previousLog) return;
        previousLog = textarea.value;
        textarea.scrollTop = textarea.scrollHeight;
    }, 250);
}
"""
