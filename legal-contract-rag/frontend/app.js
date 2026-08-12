// If the page is opened as a local file (file://) or from any other origin,
// always point API calls at the FastAPI backend on localhost:8000.
// When served by FastAPI itself (http://localhost:8000), this also works fine.
const API_BASE = (location.protocol === 'file:' || location.port !== '8000')
    ? 'http://localhost:8000'
    : '';

document.addEventListener('DOMContentLoaded', () => {
    const pdfFileInput = document.getElementById('pdfFile');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadStatus = document.getElementById('uploadStatus');
    const documentsList = document.getElementById('documentsList');
    const questionInput = document.getElementById('questionInput');
    const askBtn = document.getElementById('askBtn');
    const answerDiv = document.getElementById('answer');
    const sourcesListDiv = document.getElementById('sourcesList');
    const modelStatusIndicator = document.getElementById('model-status-indicator');

    // ─── Upload PDF ──────────────────────────────────────────────────────────
    uploadBtn.addEventListener('click', async () => {
        const file = pdfFileInput.files[0];
        if (!file) {
            showStatus(uploadStatus, 'Please select a PDF file first.', 'error');
            return;
        }
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showStatus(uploadStatus, 'Only PDF files are supported.', 'error');
            return;
        }

        showStatus(uploadStatus, 'Uploading and processing… this may take a moment.', 'info');
        uploadBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_BASE}/api/documents/upload`, {
                method: 'POST',
                body: formData   // DO NOT set Content-Type header; browser sets multipart boundary automatically
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            showStatus(
                uploadStatus,
                `✅ Success! "${data.fileName}" processed — ${data.pages} page(s), ${data.chunksCreated} chunks created.`,
                'success'
            );

            // Clear the file input
            pdfFileInput.value = '';

            // Refresh documents list
            loadDocuments();
        } catch (error) {
            const msg = error.message.includes('Failed to fetch')
                ? 'Cannot reach the server. Make sure uvicorn is running on http://localhost:8000'
                : error.message;
            showStatus(uploadStatus, `❌ Error: ${msg}`, 'error');
            console.error('Upload error:', error);
        } finally {
            uploadBtn.disabled = false;
        }
    });

    // ─── Load documents list ─────────────────────────────────────────────────
    async function loadDocuments() {
        documentsList.innerHTML = '<p>Loading…</p>';
        try {
            const response = await fetch(`${API_BASE}/api/documents/`);
            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const documents = await response.json();

            if (documents.length === 0) {
                documentsList.innerHTML = '<p class="muted">No documents uploaded yet.</p>';
                return;
            }

            documentsList.innerHTML = documents.map(doc => `
                <div class="doc-item">
                    <span class="doc-icon">📄</span>
                    <span class="doc-name">${doc.name}</span>
                    <span class="doc-meta">${doc.chunks} chunks</span>
                </div>
            `).join('');
        } catch (error) {
            documentsList.innerHTML = `<p class="error-text">Error loading documents: ${error.message}</p>`;
            console.error('Load documents error:', error);
        }
    }

    // ─── Ask question ────────────────────────────────────────────────────────
    askBtn.addEventListener('click', async () => {
        const question = questionInput.value.trim();
        if (!question) {
            answerDiv.innerHTML = '<p class="muted">Please enter a question.</p>';
            return;
        }

        answerDiv.innerHTML = '<p class="thinking">⏳ Thinking… (may take 10–30 seconds)</p>';
        sourcesListDiv.innerHTML = '<p class="muted">Searching documents…</p>';
        askBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/api/chat/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            answerDiv.innerHTML = `<p>${escapeHtml(data.answer)}</p>`;

            if (data.sources && data.sources.length > 0) {
                sourcesListDiv.innerHTML = data.sources.map(src => `
                    <div class="source-item">
                        📎 <strong>${escapeHtml(src.document)}</strong> — Page ${src.page}, Chunk ${src.chunk}
                    </div>
                `).join('');
            } else {
                sourcesListDiv.innerHTML = '<p class="muted">No specific sources cited.</p>';
            }
        } catch (error) {
            const msg = error.message.includes('Failed to fetch')
                ? 'Cannot reach the server. Make sure uvicorn is running on http://localhost:8000'
                : error.message;
            answerDiv.innerHTML = `<p class="error-text">❌ ${escapeHtml(msg)}</p>`;
            sourcesListDiv.innerHTML = '';
            console.error('Question error:', error);
        } finally {
            askBtn.disabled = false;
        }
    });

    // ─── Health check ────────────────────────────────────────────────────────
    async function checkHealth() {
        try {
            const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
            if (!response.ok) throw new Error('bad status');
            const data = await response.json();

            if (data.status === 'healthy') {
                modelStatusIndicator.textContent = '🟢 Connected';
                modelStatusIndicator.style.color = '#2ecc71';
            } else {
                modelStatusIndicator.textContent = '🟠 Degraded';
                modelStatusIndicator.style.color = '#f39c12';
            }
        } catch {
            modelStatusIndicator.textContent = '🔴 Offline';
            modelStatusIndicator.style.color = '#e74c3c';
        }
    }

    // ─── Helpers ─────────────────────────────────────────────────────────────
    function showStatus(el, msg, type) {
        el.textContent = msg;
        el.className = 'status-box ' + type;
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    // ─── Init ─────────────────────────────────────────────────────────────────
    checkHealth();
    loadDocuments();
});
