/**
 * dichvideo.com - Frontend JavaScript (Dashboard edition)
 * Quản lý kéo thả tệp, cấu hình tùy chọn động, biên tập Workspace và lịch sử dự án
 */

// ============================================================
// ELEMENTS
// ============================================================

const elements = {
    // Tabs & views
    homeTab: document.getElementById('homeTab'),
    progressTab: document.getElementById('progressTab'),
    workspaceTab: document.getElementById('workspaceTab'),
    resultTab: document.getElementById('resultTab'),
    errorTab: document.getElementById('errorTab'),
    historyTab: document.getElementById('historyTab'),
    thumbnailTab: document.getElementById('thumbnailTab'),
    srtTab: document.getElementById('srtTab'),
    settingsTab: document.getElementById('settingsTab'),
    pageTitle: document.getElementById('pageTitle'),
    historyList: document.getElementById('historyList'),

    // SRT to Audio elements
    srtGenerateBtn: document.getElementById('srtGenerateBtn'),
    srtUploadBtn: document.getElementById('srtUploadBtn'),
    srtFileInput: document.getElementById('srtFileInput'),
    srtFileStatusText: document.getElementById('srtFileStatusText'),
    srtChooseFileBtn: document.getElementById('srtChooseFileBtn'),
    srtParseBtn: document.getElementById('srtParseBtn'),
    srtTextArea: document.getElementById('srtTextArea'),
    srtParseStatus: document.getElementById('srtParseStatus'),
    srtGenderMaleBtn: document.getElementById('srtGenderMaleBtn'),
    srtGenderFemaleBtn: document.getElementById('srtGenderFemaleBtn'),
    srtVoiceSelect: document.getElementById('srtVoiceSelect'),
    srtOutputFileName: document.getElementById('srtOutputFileName'),
    srtResultActionContainer: document.getElementById('srtResultActionContainer'),
    srtDownloadAudioBtn: document.getElementById('srtDownloadAudioBtn'),

    // Home / Upload elements
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    urlInput: document.getElementById('urlInput'),
    pasteBtn: document.getElementById('pasteBtn'),
    processBtn: document.getElementById('processBtn'),
    errorMessage: document.getElementById('errorMessage'),
    seriesInput: document.getElementById('seriesInput'),
    episodeInput: document.getElementById('episodeInput'),

    // Progress elements
    progressTitle: document.getElementById('progressTitle'),
    videoTitle: document.getElementById('videoTitle'),
    overallPercent: document.getElementById('overallPercent'),
    overallProgressBar: document.getElementById('overallProgressBar'),

    // Workspace elements
    workspaceVideo: document.getElementById('workspaceVideo'),
    videoSubTitleOverlay: document.getElementById('videoSubTitleOverlay'),
    subColor: document.getElementById('subColor'),
    subSize: document.getElementById('subSize'),
    subFont: document.getElementById('subFont'),
    subBgColor: document.getElementById('subBgColor'),
    subBgOpacity: document.getElementById('subBgOpacity'),
    subOutline: document.getElementById('subOutline'),
    subOutlineWidth: document.getElementById('subOutlineWidth'),
    subShadow: document.getElementById('subShadow'),
    subBg: document.getElementById('subBg'),
    subPosition: document.getElementById('subPosition'),
    workspaceVoiceSelect: document.getElementById('workspaceVoiceSelect'),
    workspaceVoiceSpeedSelect: document.getElementById('workspaceVoiceSpeedSelect'),
    subtitleList: document.getElementById('subtitleList'),
    exportBtn: document.getElementById('exportBtn'),
    workspacePreviewBtn: document.getElementById('workspacePreviewBtn'),
    workspaceOriginalBtn: document.getElementById('workspaceOriginalBtn'),
    downloadSrtBtn: document.getElementById('downloadSrtBtn'),
    downloadThumbBtn: document.getElementById('downloadThumbBtn'),
    uploadThumbBtn: document.getElementById('uploadThumbBtn'),
    thumbFileInput: document.getElementById('thumbFileInput'),
    thumbTitleInput: document.getElementById('thumbTitleInput'),
    thumbEpInput: document.getElementById('thumbEpInput'),
    btnRegenThumbText: document.getElementById('btnRegenThumbText'),
    stThumbFile: document.getElementById('stThumbFile'),
    stThumbTitle: document.getElementById('stThumbTitle'),
    stThumbEp: document.getElementById('stThumbEp'),
    stThumbTime: document.getElementById('stThumbTime'),
    btnGenerateStThumb: document.getElementById('btnGenerateStThumb'),
    editorRegenAudioBtn: document.getElementById('editorRegenAudioBtn'),
    editorVideoTitle: document.getElementById('editorVideoTitle'),
    editorVideoMeta: document.getElementById('editorVideoMeta'),
    wsOriginalVolume: document.getElementById('wsOriginalVolume'),
    wsOriginalVolumeVal: document.getElementById('wsOriginalVolumeVal'),
    wsDubbedVolume: document.getElementById('wsDubbedVolume'),
    wsDubbedVolumeVal: document.getElementById('wsDubbedVolumeVal'),

    // Custom Video Controls Elements
    customVideoControls: document.getElementById('customVideoControls'),
    videoProgressContainer: document.getElementById('videoProgressContainer'),
    videoProgressFill: document.getElementById('videoProgressFill'),
    videoProgressHandle: document.getElementById('videoProgressHandle'),
    ctrlPrevSub: document.getElementById('ctrlPrevSub'),
    ctrlPlayPause: document.getElementById('ctrlPlayPause'),
    playIcon: document.getElementById('playIcon'),
    pauseIcon: document.getElementById('pauseIcon'),
    ctrlNextSub: document.getElementById('ctrlNextSub'),
    ctrlTimeDisplay: document.getElementById('ctrlTimeDisplay'),
    ctrlMute: document.getElementById('ctrlMute'),
    volumeUpIcon: document.getElementById('volumeUpIcon'),
    volumeMuteIcon: document.getElementById('volumeMuteIcon'),
    ctrlVolumeSlider: document.getElementById('ctrlVolumeSlider'),
    ctrlTrackBtn: document.getElementById('ctrlTrackBtn'),
    ctrlTrackMenu: document.getElementById('ctrlTrackMenu'),
    menuAudioOriginal: document.getElementById('menuAudioOriginal'),
    menuAudioDubbed: document.getElementById('menuAudioDubbed'),
    ctrlSubToggle: document.getElementById('ctrlSubToggle'),
    ctrlFullscreen: document.getElementById('ctrlFullscreen'),

    // Workspace internal tabs
    tabBtnSubtitles: document.getElementById('tabBtnSubtitles'),
    tabBtnStyling: document.getElementById('tabBtnStyling'),
    wsTabSubtitles: document.getElementById('wsTabSubtitles'),
    wsTabStyling: document.getElementById('wsTabStyling'),

    // Result elements
    resultTitle: document.getElementById('resultTitle'),
    downloadBtn: document.getElementById('downloadBtn'),
    downloadSrtBtn: document.getElementById('downloadSrtBtn'),
    newJobBtn: document.getElementById('newJobBtn'),
    editAgainBtn: document.getElementById('editAgainBtn'),

    // Error elements
    errorDetail: document.getElementById('errorDetail'),
    retryBtn: document.getElementById('retryBtn'),
};

// ============================================================
// CONFIG STATE
// ============================================================

let currentJobId = null;
let originalVideoUrl = null;
let uploadedJobId = null;  // Lưu job_id sau khi upload file local thành công
let websocket = null;
let reconnectTimer = null;
let currentSegments = [];
let jobsCache = null;

// Cấu hình tham số mặc định
const configs = {
    model_size: 'base',
    source_lang: 'en',
    voice: 'vi-VN-HoaiMyNeural',
    voice_speed: 1.0,
    original_volume: 0.15,
    video_quality: 'best',
    separate_vocals: false
};

function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

// ============================================================
// TAB TRANSITIONS HELPERS
// ============================================================

function showTab(tabId) {
    const tabs = ['homeTab', 'progressTab', 'workspaceTab', 'resultTab', 'errorTab', 'historyTab', 'thumbnailTab', 'srtTab', 'settingsTab'];
    
    tabs.forEach(id => {
        const el = elements[id];
        if (!el) return;
        if (id === tabId) {
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    });

    // Cập nhật trạng thái class active cho Sidebar menu tương ứng
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    if (tabId === 'homeTab') {
        elements.pageTitle.textContent = 'Trang chủ';
        const homeNav = document.querySelector('.nav-item[data-tab="home"]');
        if (homeNav) homeNav.classList.add('active');
    } else if (tabId === 'historyTab') {
        elements.pageTitle.textContent = 'Lịch sử';
        const histNav = document.querySelector('.nav-item[data-tab="history"]');
        if (histNav) histNav.classList.add('active');
    } else if (tabId === 'workspaceTab') {
        elements.pageTitle.textContent = 'Trình chỉnh sửa';
        const editorNav = document.querySelector('.nav-item[data-tab="editor"]');
        if (editorNav) editorNav.classList.add('active');
    } else if (tabId === 'thumbnailTab') {
        elements.pageTitle.textContent = 'Tạo Thumbnail';
        const thumbNav = document.querySelector('.nav-item[data-tab="thumbnail"]');
        if (thumbNav) thumbNav.classList.add('active');
    } else if (tabId === 'srtTab') {
        elements.pageTitle.textContent = 'SRT sang Audio';
        const srtNav = document.querySelector('.nav-item[data-tab="srt"]');
        if (srtNav) srtNav.classList.add('active');
        updateSrtOutputFileName();
    } else if (tabId === 'progressTab') {
        elements.pageTitle.textContent = 'Đang xử lý';
    } else if (tabId === 'resultTab') {
        elements.pageTitle.textContent = 'Hoàn thành';
    } else if (tabId === 'errorTab') {
        elements.pageTitle.textContent = 'Lỗi hệ thống';
    } else if (tabId === 'settingsTab') {
        elements.pageTitle.textContent = 'Cài đặt';
        const settingsNav = document.querySelector('.nav-item[data-tab="settings"]');
        if (settingsNav) settingsNav.classList.add('active');
    }
}

function updateSrtOutputFileName() {
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    
    if (elements.srtOutputFileName) {
        elements.srtOutputFileName.textContent = `srt-sang-audio-${yyyy}${mm}${dd}-${hh}${min}${ss}.mp3`;
    }
}

function showError(message) {
    elements.errorMessage.textContent = message;
    elements.errorMessage.classList.remove('hidden');
    setTimeout(() => {
        elements.errorMessage.classList.add('hidden');
    }, 8000);
}

function resetProgressSteps() {
    document.querySelectorAll('.step').forEach(step => {
        step.className = 'step pending';
        const fill = step.querySelector('.step-progress-fill');
        if (fill) fill.style.width = '0%';
        const msg = step.querySelector('.step-message');
        if (msg) msg.textContent = '';
    });
    elements.overallProgressBar.style.width = '0%';
    elements.overallPercent.textContent = '0%';
}

// ============================================================
// DRAG & DROP + LOCAL FILE UPLOAD LOGIC
// ============================================================

// Highlight drop zone khi kéo file
if (elements.dropZone) {
    ['dragenter', 'dragover'].forEach(eventName => {
        elements.dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            elements.dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        elements.dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            elements.dropZone.classList.remove('dragover');
        }, false);
    });

    // Xử lý khi thả file (drop)
    elements.dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            elements.fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });
}

// Xử lý khi click chọn file
if (elements.fileInput) {
    elements.fileInput.addEventListener('change', (e) => {
        if (elements.fileInput.files.length > 0) {
            handleFileSelect(elements.fileInput.files[0]);
        }
    });
}

/**
 * Thực hiện upload file video lên FastAPI
 */
async function handleFileSelect(file) {
    // Show visual feedback in drop zone
    const dropContent = elements.dropZone.querySelector('.drop-zone-content');
    dropContent.innerHTML = `
        <span class="upload-icon">⏳</span>
        <p class="drop-text">Đang tải lên: ${file.name}</p>
        <p class="drop-sub">Vui lòng chờ giây lát...</p>
    `;
    
    // Clear URL input
    elements.urlInput.value = '';
    elements.processBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Không thể tải file lên server.');

        const data = await response.json();
        uploadedJobId = data.job_id;

        // Upload thành công
        dropContent.innerHTML = `
            <span class="upload-icon">✅</span>
            <p class="drop-text" style="color: var(--success)">Đã tải lên thành công!</p>
            <p class="drop-sub">${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)</p>
        `;
        
        // Bật nút xử lý
        elements.processBtn.disabled = false;

    } catch (e) {
        dropContent.innerHTML = `
            <span class="upload-icon">❌</span>
            <p class="drop-text" style="color: var(--error)">Lỗi tải lên</p>
            <p class="drop-sub">${e.message}</p>
        `;
        uploadedJobId = null;
        elements.processBtn.disabled = true;
    }
}

// ============================================================
// SELECT CONFIGS LOGIC
// ============================================================

// Lắng nghe click các ô cấu hình (grid options)
document.querySelectorAll('.config-options').forEach(group => {
    const configName = group.getAttribute('data-config');
    group.querySelectorAll('.option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            group.querySelectorAll('.option-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Cập nhật cấu hình
            const val = btn.getAttribute('data-value');
            if (configName === 'original_volume') {
                configs[configName] = parseFloat(val);
            } else {
                configs[configName] = val;
            }
            
            // Đồng bộ giọng đọc xuống ô select giọng đọc của Workspace
            if (configName === 'voice') {
                elements.workspaceVoiceSelect.value = val;
            }
        });
    });
});

// Đồng bộ ngược lại nếu thay đổi giọng đọc trong Workspace review
if (elements.workspaceVoiceSelect) {
    elements.workspaceVoiceSelect.addEventListener('change', (e) => {
        configs.voice = e.target.value;
    });
}
if (elements.workspaceVoiceSpeedSelect) {
    elements.workspaceVoiceSpeedSelect.addEventListener('change', (e) => {
        configs.voice_speed = parseFloat(e.target.value);
    });
}

// URL input thay đổi
if (elements.urlInput) {
    elements.urlInput.addEventListener('input', () => {
        const url = elements.urlInput.value.trim();
        if (isValidUrl(url)) {
            elements.processBtn.disabled = false;
            
            // Reset drop zone nếu trước đó đã upload
            if (uploadedJobId) {
                uploadedJobId = null;
                elements.dropZone.querySelector('.drop-zone-content').innerHTML = `
                    <span class="upload-icon">📤</span>
                    <p class="drop-text">Thả tập tin vào đây</p>
                    <p class="drop-sub">Hoặc nhấn để chọn video từ máy tính</p>
                `;
                elements.fileInput.value = '';
            }
        } else {
            if (!uploadedJobId) {
                elements.processBtn.disabled = true;
            }
        }
    });
}

// Paste button URL
if (elements.pasteBtn) {
    elements.pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            elements.urlInput.value = text;
            elements.urlInput.dispatchEvent(new Event('input'));
        } catch {
            showError('Không thể tự động đọc clipboard. Hãy dán thủ công (Ctrl+V).');
        }
    });
}

// ============================================================
// TIMELINE AUDIO SYNC & RENDER LOGIC
// ============================================================

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function renderSubtitleList(segments) {
    elements.subtitleList.innerHTML = '';
    currentSegments = [...segments];

    segments.forEach((seg) => {
        const card = document.createElement('div');
        card.className = 'subtitle-row-card';
        card.setAttribute('data-index', seg.index);

        card.innerHTML = `
            <div class="subtitle-time-badge">${formatTimeMs(seg.start)}</div>
            <div class="subtitle-text-content">
                <div class="subtitle-original-text">${seg.original_text || seg.text}</div>
                <textarea class="subtitle-translated-input" placeholder="Nhập bản dịch tiếng Việt...">${seg.text || ''}</textarea>
            </div>
            <div class="subtitle-action-buttons">
                <button class="subtitle-split-btn" title="Cắt đôi câu tại vị trí con trỏ">✂️</button>
                <button class="subtitle-merge-btn" title="Gộp với câu tiếp theo">🔗</button>
                <button class="subtitle-delete-btn" title="Xoá câu này">🗑️</button>
            </div>
        `;

        // Tua video khi click vào badge thời gian hoặc vùng text
        card.addEventListener('click', (e) => {
            if (e.target.tagName.toLowerCase() !== 'textarea' && !e.target.closest('.subtitle-action-buttons')) {
                elements.workspaceVideo.currentTime = seg.start;
                elements.workspaceVideo.play().catch(() => {});
            }
        });

        // Sửa bản dịch + Tự động co giãn textarea theo nội dung
        const textarea = card.querySelector('.subtitle-translated-input');
        
        const resizeTextarea = () => {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        };

        // Kích hoạt co giãn ngay sau khi render xong DOM
        setTimeout(resizeTextarea, 0);

        textarea.addEventListener('input', (e) => {
            const val = e.target.value;
            const index = currentSegments.findIndex(s => s.index === seg.index);
            if (index !== -1) {
                currentSegments[index].text = val;
            }
            
            // Co giãn textarea khi gõ chữ
            resizeTextarea();

            // Cập nhật text phụ đề nổi trên video player ngay lập tức
            const video = elements.workspaceVideo;
            if (video) {
                const curTime = video.currentTime;
                if (curTime >= seg.start && curTime <= seg.end) {
                    const overlay = elements.videoSubTitleOverlay;
                    if (overlay) {
                        overlay.textContent = val;
                        overlay.style.display = (val && val.trim()) ? 'block' : 'none';
                        applySubtitleOverlayStyles(overlay);
                    }
                }
            }
        });

        // Xử lý Cắt câu
        const splitBtn = card.querySelector('.subtitle-split-btn');
        splitBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            splitSegment(seg, textarea);
        });

        // Xử lý Gộp câu
        const mergeBtn = card.querySelector('.subtitle-merge-btn');
        const indexInArr = segments.findIndex(s => s.index === seg.index);
        if (indexInArr === segments.length - 1) {
            mergeBtn.style.display = 'none';
        }
        mergeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            mergeSegment(seg);
        });

        // Xoá câu phụ đề
        const deleteBtn = card.querySelector('.subtitle-delete-btn');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm(`Bạn có chắc chắn muốn xoá câu phụ đề này?`)) {
                currentSegments = currentSegments.filter(s => s.index !== seg.index);
                // Đánh lại số thứ tự index
                currentSegments.forEach((s, idx) => {
                    s.index = idx + 1;
                });
                renderSubtitleList(currentSegments);
            }
        });

        elements.subtitleList.appendChild(card);
    });
}

function splitSegment(seg, textarea) {
    const fullText = textarea.value;
    const cursorPos = textarea.selectionStart;
    
    let text1 = "";
    let text2 = "";
    let splitPos = cursorPos;
    
    // Nếu con trỏ ở vị trí 0 hoặc cuối (chưa focus hoặc chưa chọn vị trí)
    // thì ta tự động tìm khoảng trắng gần trung điểm nhất để cắt
    if (cursorPos === 0 || cursorPos === fullText.length) {
        const mid = Math.round(fullText.length / 2);
        const beforeSpace = fullText.lastIndexOf(' ', mid);
        const afterSpace = fullText.indexOf(' ', mid);
        if (beforeSpace !== -1 && (mid - beforeSpace < afterSpace - mid || afterSpace === -1)) {
            splitPos = beforeSpace;
        } else if (afterSpace !== -1) {
            splitPos = afterSpace;
        } else {
            splitPos = mid;
        }
    }
    
    text1 = fullText.substring(0, splitPos).trim();
    text2 = fullText.substring(splitPos).trim();
    
    if (!text1 || !text2) {
        alert("Không thể cắt phân đoạn rỗng hoặc phân đoạn chỉ có 1 từ!");
        return;
    }
    
    const ratio = fullText.length > 0 ? (splitPos / fullText.length) : 0.5;
    
    // Tách văn bản gốc tương tự theo tỷ lệ
    const origText = seg.original_text || seg.text || "";
    let origSplitPos = Math.round(origText.length * ratio);
    const origBeforeSpace = origText.lastIndexOf(' ', origSplitPos);
    const origAfterSpace = origText.indexOf(' ', origSplitPos);
    if (origBeforeSpace !== -1 && (origSplitPos - origBeforeSpace < origAfterSpace - origSplitPos || origAfterSpace === -1)) {
        origSplitPos = origBeforeSpace;
    } else if (origAfterSpace !== -1) {
        origSplitPos = origAfterSpace;
    }
    
    const orig1 = origText.substring(0, origSplitPos).trim();
    const orig2 = origText.substring(origSplitPos).trim();
    
    // Phân chia thời lượng
    const duration = seg.end - seg.start;
    const splitTime = seg.start + (duration * ratio);
    
    const newSeg1 = {
        index: seg.index,
        start: seg.start,
        end: splitTime,
        original_text: orig1,
        text: text1
    };
    
    const newSeg2 = {
        index: seg.index + 0.5,
        start: splitTime,
        end: seg.end,
        original_text: orig2,
        text: text2
    };
    
    const indexInArray = currentSegments.findIndex(s => s.index === seg.index);
    if (indexInArray !== -1) {
        currentSegments.splice(indexInArray, 1, newSeg1, newSeg2);
        // Sắp xếp lại theo start time để đảm bảo thứ tự
        currentSegments.sort((a, b) => a.start - b.start);
        // Đánh lại số thứ tự index
        currentSegments.forEach((s, idx) => {
            s.index = idx + 1;
        });
        renderSubtitleList(currentSegments);
    }
}

function mergeSegment(seg) {
    const indexInArray = currentSegments.findIndex(s => s.index === seg.index);
    if (indexInArray === -1 || indexInArray === currentSegments.length - 1) {
        alert("Không có câu tiếp theo để gộp!");
        return;
    }
    
    const nextSeg = currentSegments[indexInArray + 1];
    
    const mergedText = (seg.text.trim() + " " + nextSeg.text.trim()).trim();
    const mergedOrig = ((seg.original_text || seg.text).trim() + " " + (nextSeg.original_text || nextSeg.text).trim()).trim();
    
    const mergedSeg = {
        index: seg.index,
        start: seg.start,
        end: nextSeg.end,
        original_text: mergedOrig,
        text: mergedText
    };
    
    currentSegments.splice(indexInArray, 2, mergedSeg);
    // Sắp xếp lại và đánh lại chỉ mục
    currentSegments.sort((a, b) => a.start - b.start);
    currentSegments.forEach((s, idx) => {
        s.index = idx + 1;
    });
    renderSubtitleList(currentSegments);
}

function initializeWorkspaceSliders(data) {
    if (elements.wsOriginalVolume && data.original_volume !== undefined) {
        elements.wsOriginalVolume.value = data.original_volume;
        if (elements.wsOriginalVolumeVal) {
            elements.wsOriginalVolumeVal.textContent = Math.round(data.original_volume * 100) + '%';
        }
    }
    if (elements.wsDubbedVolume && data.dubbed_volume !== undefined) {
        elements.wsDubbedVolume.value = data.dubbed_volume;
        if (elements.wsDubbedVolumeVal) {
            elements.wsDubbedVolumeVal.textContent = Math.round(data.dubbed_volume * 100) + '%';
        }
    }
    const wsSeparateVocals = document.getElementById('wsSeparateVocals');
    if (wsSeparateVocals && data.separate_vocals !== undefined) {
        wsSeparateVocals.checked = !!data.separate_vocals;
    }
}

function populateWorkspaceFolderSelect(folders) {
    const select = document.getElementById('wsOutputFolderSelect');
    if (!select) return;
    
    // Lưu lại giá trị đang chọn
    const currentVal = select.value;
    
    let html = `
        <option value="default">📁 Mặc định (Thư mục outputs/)</option>
        <option value="custom">⚙️ Nhập đường dẫn thư mục tùy chọn...</option>
    `;
    
    if (folders && folders.length > 0) {
        html += '<optgroup label="Thư mục đã tạo">';
        folders.forEach(f => {
            html += `<option value="${f}">📁 Thư mục: ${f}</option>`;
        });
        html += '</optgroup>';
    }
    
    select.innerHTML = html;
    
    // Phục hồi lại giá trị đang chọn nếu còn tồn tại
    if (Array.from(select.options).some(opt => opt.value === currentVal)) {
        select.value = currentVal;
    } else {
        select.value = 'default';
    }
}

function hexToRgba(hex, opacityPercent) {
    if (!hex) return 'rgba(0,0,0,0.7)';
    let c;
    if(/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)){
        c= hex.substring(1).split('');
        if(c.length== 3){
            c= [c[0], c[0], c[1], c[1], c[2], c[2]];
        }
        c= '0x' + c.join('');
        return 'rgba('+[(c>>16)&255, (c>>8)&255, c&255].join(',')+','+(opacityPercent/100)+')';
    }
    return 'rgba(0,0,0,0.7)';
}

function applySubtitleOverlayStyles(overlay) {
    if (!overlay) return;
    
    const video = elements.workspaceVideo;
    
    // 1. Màu sắc chữ
    const color = elements.subColor ? elements.subColor.value : '#ffffff';
    overlay.style.color = color;
    
    // 2. Font chữ
    const font = elements.subFont ? elements.subFont.value : 'Arial';
    overlay.style.fontFamily = font;
    
    // Tính toán kích thước hiển thị thực tế của video trong player
    let activeWidth = 640;
    let activeHeight = 360;
    let blackBarHeight = 0;
    let videoRatio = 1.777; // Mặc định 16:9
    
    if (video && video.videoWidth && video.videoHeight) {
        videoRatio = video.videoWidth / video.videoHeight;
        const playerWidth = video.clientWidth;
        const playerHeight = video.clientHeight;
        const playerRatio = playerWidth / playerHeight;
        
        if (playerRatio > videoRatio) {
            activeWidth = playerHeight * videoRatio;
            activeHeight = playerHeight;
        } else {
            activeWidth = playerWidth;
            activeHeight = playerWidth / videoRatio;
            blackBarHeight = (playerHeight - activeHeight) / 2;
        }
    } else if (video) {
        activeWidth = video.clientWidth || 640;
        activeHeight = video.clientHeight || 360;
    }
    
    // 3. Kích thước chữ (Tính tỷ lệ chuẩn so với virtual 288px của FFmpeg, tự động thu nhỏ nếu video dọc/vuông)
    const rawSize = elements.subSize ? parseInt(elements.subSize.value) : 22;
    let scaleFactor = 1.0;
    if (videoRatio < 1.6) {
        scaleFactor = videoRatio / 1.777;
    }
    const targetSize = rawSize * scaleFactor;
    const scaledSize = Math.max(12, Math.round((targetSize / 288) * activeHeight));
    overlay.style.fontSize = scaledSize + 'px';
    
    // 4. Kiểu nền chữ & Độ mờ nền
    const bgType = elements.subBg ? elements.subBg.value : 'none';
    const bgColor = elements.subBgColor ? elements.subBgColor.value : '#000000';
    const bgOpacity = elements.subBgOpacity ? parseInt(elements.subBgOpacity.value) : 0;
    
    if (bgType === 'box') {
        overlay.style.background = hexToRgba(bgColor, bgOpacity);
        overlay.style.padding = '6px 12px';
        overlay.style.borderRadius = '6px';
    } else {
        overlay.style.background = 'transparent';
        overlay.style.padding = '0';
        overlay.style.borderRadius = '0';
    }
    
    // 5. Viền chữ (Outline) & Bóng chữ (Shadow)
    // Sử dụng kỹ thuật text-shadow đa hướng để tránh viền đen lấn đè làm đen ngóm ruột chữ
    const hasOutline = elements.subOutline ? elements.subOutline.checked : true;
    const outlineWidth = elements.subOutlineWidth ? parseInt(elements.subOutlineWidth.value) : 4;
    const hasShadow = elements.subShadow ? elements.subShadow.checked : false;
    
    const getTextOutlineShadow = (w, color) => {
        const steps = 16;
        const shadows = [];
        for (let i = 0; i < steps; i++) {
            const angle = (i * 2 * Math.PI) / steps;
            const x = (Math.cos(angle) * w).toFixed(1);
            const y = (Math.sin(angle) * w).toFixed(1);
            shadows.push(`${x}px ${y}px 0px ${color}`);
        }
        return shadows.join(', ');
    };

    overlay.style.webkitTextStroke = '0px transparent'; // Tắt hẳn text-stroke bị lỗi
    
    let finalShadow = '';
    if (hasOutline) {
        // Điều chỉnh hệ số tỷ lệ để viền hiển thị vừa vặn và sắc nét
        const scaledOutlineWidth = Math.max(0.8, (outlineWidth / 288) * activeHeight * 0.45);
        finalShadow = getTextOutlineShadow(scaledOutlineWidth, '#000000');
    }
    
    if (hasShadow) {
        const shadowPart = '3px 3px 6px rgba(0, 0, 0, 0.8)';
        finalShadow = finalShadow ? `${finalShadow}, ${shadowPart}` : shadowPart;
    }
    
    overlay.style.textShadow = finalShadow || 'none';
    
    // Giới hạn max-width phụ đề bằng 90% chiều rộng hiển thị thực của video để không bị tràn ra ngoài biên video
    overlay.style.maxWidth = Math.floor(activeWidth * 0.9) + 'px';
    
    // 4. Vị trí phụ đề
    const position = elements.subPosition ? elements.subPosition.value : 'bottom';
    let marginPercent = configs.sub_margin_v_percent !== undefined ? configs.sub_margin_v_percent : 12;
    
    if (position === 'bottom') {
        const bottomPx = Math.max(40, Math.round((marginPercent / 100) * activeHeight + blackBarHeight));
        overlay.style.bottom = bottomPx + 'px';
        overlay.style.top = 'auto';
        overlay.style.transform = 'translateX(-50%)';
    } else if (position === 'center') {
        overlay.style.top = '50%';
        overlay.style.bottom = 'auto';
        overlay.style.transform = 'translate(-50%, -50%)';
    } else if (position === 'top') {
        const topPx = Math.max(10, Math.round((marginPercent / 100) * activeHeight + blackBarHeight));
        overlay.style.top = topPx + 'px';
        overlay.style.bottom = 'auto';
        overlay.style.transform = 'translateX(-50%)';
    }
}

// ============================================================
// SUBTITLE DRAGGING LOGIC
// ============================================================
let isDraggingSub = false;
let subDragStartY = 0;
let subDragStartMarginPercent = 12;

function setupSubtitleDrag() {
    const overlay = elements.videoSubTitleOverlay;
    if (!overlay) return;

    // Enable pointer events for dragging
    overlay.style.pointerEvents = 'auto';
    overlay.style.cursor = 'grab';

    overlay.addEventListener('mousedown', (e) => {
        if (e.button !== 0) return; // Left click only
        
        isDraggingSub = true;
        subDragStartY = e.clientY;
        subDragStartMarginPercent = configs.sub_margin_v_percent !== undefined ? configs.sub_margin_v_percent : 12;
        
        overlay.style.cursor = 'grabbing';
        e.preventDefault();
        e.stopPropagation(); // Avoid triggering video container play/pause toggle
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDraggingSub) return;

        const video = elements.workspaceVideo;
        if (!video) return;

        let activeHeight = 360;
        let videoRatio = 1.777;
        if (video.videoWidth && video.videoHeight) {
            videoRatio = video.videoWidth / video.videoHeight;
            const playerWidth = video.clientWidth;
            const playerHeight = video.clientHeight;
            const playerRatio = playerWidth / playerHeight;
            if (playerRatio > videoRatio) {
                activeHeight = playerHeight;
            } else {
                activeHeight = playerWidth / videoRatio;
            }
        } else {
            activeHeight = video.clientHeight || 360;
        }

        const deltaY = e.clientY - subDragStartY;
        const deltaPercent = (deltaY / activeHeight) * 100;
        
        const position = elements.subPosition ? elements.subPosition.value : 'bottom';
        let newPercent = subDragStartMarginPercent;

        if (position === 'bottom') {
            newPercent = subDragStartMarginPercent - deltaPercent;
        } else if (position === 'top') {
            newPercent = subDragStartMarginPercent + deltaPercent;
        }

        // Limit range between 2% and 85% to keep subtitle visible in viewport
        newPercent = Math.max(2, Math.min(85, newPercent));
        configs.sub_margin_v_percent = newPercent;

        applySubtitleOverlayStyles(overlay);
    });

    window.addEventListener('mouseup', () => {
        if (isDraggingSub) {
            isDraggingSub = false;
            overlay.style.cursor = 'grab';
        }
    });
}

// ============================================================
// CUSTOM VIDEO CONTROLS LOGIC
// ============================================================
let isCustomControlsSetup = false;
let isDraggingProgress = false;

function formatTimeMs(seconds) {
    if (isNaN(seconds) || seconds === Infinity) return "00:00.00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
}

function updateCustomProgress() {
    const video = elements.workspaceVideo;
    if (!video) return;

    // Cập nhật text time display
    if (elements.ctrlTimeDisplay) {
        elements.ctrlTimeDisplay.textContent = `${formatTimeMs(video.currentTime)} / ${formatTimeMs(video.duration)}`;
    }

    // Cập nhật progress bar
    if (video.duration) {
        const pct = (video.currentTime / video.duration) * 100;
        if (elements.videoProgressFill) {
            elements.videoProgressFill.style.width = pct + '%';
        }
        if (elements.videoProgressHandle) {
            elements.videoProgressHandle.style.left = pct + '%';
        }
    }
}

function setupCustomVideoControls() {
    const video = elements.workspaceVideo;
    if (!video) return;

    // 1. Play / Pause button
    const togglePlay = () => {
        if (video.paused || video.ended) {
            video.play().catch(() => {});
        } else {
            video.pause();
        }
    };

    if (elements.ctrlPlayPause) {
        elements.ctrlPlayPause.addEventListener('click', togglePlay);
    }
    
    // Play/Pause khi click trực tiếp vào video
    video.addEventListener('click', togglePlay);

    // Đồng bộ class paused trên container để hiện controls khi pause
    const videoContainer = document.querySelector('.preview-container');
    video.addEventListener('play', () => {
        if (videoContainer) videoContainer.classList.remove('paused');
        if (elements.playIcon) elements.playIcon.classList.add('hidden');
        if (elements.pauseIcon) elements.pauseIcon.classList.remove('hidden');
    });

    video.addEventListener('pause', () => {
        if (videoContainer) videoContainer.classList.add('paused');
        if (elements.playIcon) elements.playIcon.classList.add('hidden');
        if (elements.pauseIcon) elements.pauseIcon.classList.remove('hidden');
    });
    
    // Thêm class paused ban đầu nếu video đang pause
    if (video.paused && videoContainer) {
        videoContainer.classList.add('paused');
    }

    // 2. Tua câu trước / Câu tiếp
    if (elements.ctrlPrevSub) {
        elements.ctrlPrevSub.addEventListener('click', () => {
            if (!currentSegments || currentSegments.length === 0) return;
            const curTime = video.currentTime;
            let prevSeg = null;
            
            // Duyệt từ cuối lên đầu để tìm segment trước đó
            for (let i = currentSegments.length - 1; i >= 0; i--) {
                if (currentSegments[i].start < curTime - 0.5) {
                    prevSeg = currentSegments[i];
                    break;
                }
            }
            if (prevSeg) {
                video.currentTime = prevSeg.start;
            } else {
                video.currentTime = 0;
            }
        });
    }

    if (elements.ctrlNextSub) {
        elements.ctrlNextSub.addEventListener('click', () => {
            if (!currentSegments || currentSegments.length === 0) return;
            const curTime = video.currentTime;
            // Tìm segment đầu tiên bắt đầu sau curTime + 0.2
            const nextSeg = currentSegments.find(s => s.start > curTime + 0.2);
            if (nextSeg) {
                video.currentTime = nextSeg.start;
            }
        });
    }

    // 3. Tiến trình video progress bar (Tua)
    const setVideoProgress = (e) => {
        if (!video.duration || !elements.videoProgressContainer) return;
        const rect = elements.videoProgressContainer.getBoundingClientRect();
        const padding = 16; // Khớp với padding 16px trong CSS
        const barWidth = rect.width - (padding * 2);
        let x = e.clientX - rect.left - padding;
        if (x < 0) x = 0;
        if (x > barWidth) x = barWidth;
        const pct = x / barWidth;
        video.currentTime = pct * video.duration;
    };

    if (elements.videoProgressContainer) {
        elements.videoProgressContainer.addEventListener('mousedown', (e) => {
            isDraggingProgress = true;
            setVideoProgress(e);
        });

        window.addEventListener('mousemove', (e) => {
            if (isDraggingProgress) {
                setVideoProgress(e);
            }
        });

        window.addEventListener('mouseup', () => {
            isDraggingProgress = false;
        });
    }

    // 4. Volume controls
    if (elements.ctrlVolumeSlider) {
        elements.ctrlVolumeSlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            video.volume = val;
            video.muted = (val === 0);
            updateVolumeUI(val, video.muted);
        });
    }

    if (elements.ctrlMute) {
        elements.ctrlMute.addEventListener('click', () => {
            video.muted = !video.muted;
            updateVolumeUI(video.volume, video.muted);
        });
    }

    const updateVolumeUI = (volume, muted) => {
        if (muted || volume === 0) {
            if (elements.volumeUpIcon) elements.volumeUpIcon.classList.add('hidden');
            if (elements.volumeMuteIcon) elements.volumeMuteIcon.classList.remove('hidden');
            if (elements.ctrlVolumeSlider) elements.ctrlVolumeSlider.value = 0;
        } else {
            if (elements.volumeUpIcon) elements.volumeUpIcon.classList.remove('hidden');
            if (elements.volumeMuteIcon) elements.volumeMuteIcon.classList.add('hidden');
            if (elements.ctrlVolumeSlider) elements.ctrlVolumeSlider.value = volume;
        }
    };

    // 5. Track menu
    if (elements.ctrlTrackBtn) {
        elements.ctrlTrackBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (elements.ctrlTrackMenu) {
                elements.ctrlTrackMenu.classList.toggle('hidden');
            }
        });
    }

    window.addEventListener('click', () => {
        if (elements.ctrlTrackMenu) {
            elements.ctrlTrackMenu.classList.add('hidden');
        }
    });

    if (elements.ctrlTrackMenu) {
        elements.ctrlTrackMenu.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    if (elements.menuAudioOriginal) {
        elements.menuAudioOriginal.addEventListener('click', () => {
            if (elements.workspaceOriginalBtn) {
                elements.workspaceOriginalBtn.click();
                if (elements.ctrlTrackMenu) elements.ctrlTrackMenu.classList.add('hidden');
            }
        });
    }

    if (elements.menuAudioDubbed) {
        elements.menuAudioDubbed.addEventListener('click', () => {
            if (elements.workspacePreviewBtn) {
                elements.workspacePreviewBtn.click();
                if (elements.ctrlTrackMenu) elements.ctrlTrackMenu.classList.add('hidden');
            }
        });
    }

    // Tốc độ phát
    const speedItems = document.querySelectorAll('.track-menu [data-speed]');
    speedItems.forEach(item => {
        item.addEventListener('click', () => {
            const speed = parseFloat(item.getAttribute('data-speed'));
            video.playbackRate = speed;
            
            speedItems.forEach(si => si.classList.remove('active'));
            item.classList.add('active');
            if (elements.ctrlTrackMenu) elements.ctrlTrackMenu.classList.add('hidden');
        });
    });

    // 6. Subtitle Toggle
    if (elements.ctrlSubToggle) {
        elements.ctrlSubToggle.addEventListener('click', () => {
            const isActive = elements.ctrlSubToggle.classList.toggle('active');
            const overlay = elements.videoSubTitleOverlay;
            if (overlay) {
                if (isActive) {
                    const curTime = video.currentTime;
                    const activeSeg = currentSegments.find(s => curTime >= s.start && curTime <= s.end);
                    if (activeSeg && activeSeg.text && activeSeg.text.trim()) {
                        overlay.textContent = activeSeg.text;
                        overlay.style.display = 'block';
                        applySubtitleOverlayStyles(overlay);
                    }
                } else {
                    overlay.style.display = 'none';
                }
            }
        });
    }

    // 7. Fullscreen Toggle
    if (elements.ctrlFullscreen) {
        elements.ctrlFullscreen.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                if (videoContainer) {
                    videoContainer.requestFullscreen().catch(err => {
                        console.error("Fullscreen error:", err);
                    });
                }
            } else {
                document.exitFullscreen();
            }
        });
    }
}

function setupVideoSync() {
    const video = elements.workspaceVideo;
    if (!video) return;

    if (!isCustomControlsSetup) {
        setupCustomVideoControls();
        setupSubtitleDrag();
        isCustomControlsSetup = true;
    }

    // Reset selectors when changing/loading video
    if (elements.menuAudioOriginal && elements.menuAudioDubbed) {
        elements.menuAudioOriginal.classList.add('active');
        elements.menuAudioDubbed.classList.remove('active');
    }
    video.playbackRate = 1.0;
    const speedItems = document.querySelectorAll('.track-menu [data-speed]');
    speedItems.forEach(si => {
        if (parseFloat(si.getAttribute('data-speed')) === 1.0) {
            si.classList.add('active');
        } else {
            si.classList.remove('active');
        }
    });

    video.addEventListener('timeupdate', () => {
        const curTime = video.currentTime;
        const activeSeg = currentSegments.find(s => curTime >= s.start && curTime <= s.end);
        
        const overlay = elements.videoSubTitleOverlay;
        if (overlay) {
            if (activeSeg && activeSeg.text && activeSeg.text.trim()) {
                overlay.textContent = activeSeg.text;
                overlay.style.display = 'block';
                applySubtitleOverlayStyles(overlay);
            } else {
                overlay.style.display = 'none';
            }
        }
        
        if (activeSeg) {
            const activeEl = document.querySelector(`.subtitle-row-card[data-index="${activeSeg.index}"]`);
            if (activeEl) {
                document.querySelectorAll('.subtitle-row-card').forEach(el => el.classList.remove('active'));
                activeEl.classList.add('active');
                
                const listContainer = document.querySelector('.workspace-left');
                if (listContainer) {
                    const itemTop = activeEl.getBoundingClientRect().top - listContainer.getBoundingClientRect().top + listContainer.scrollTop;
                    const itemHeight = activeEl.clientHeight;
                    const containerHeight = listContainer.clientHeight;
                    const currentScroll = listContainer.scrollTop;

                    if (itemTop < currentScroll || (itemTop + itemHeight) > (currentScroll + containerHeight)) {
                        listContainer.scrollTo({
                            top: itemTop - (containerHeight / 2) + (itemHeight / 2),
                            behavior: 'smooth'
                        });
                    }
                }
            }
        }
        updateCustomProgress();
    });

    // Ép tính toán lại khi metadata tải xong hoặc thay đổi kích cỡ màn hình
    video.addEventListener('loadedmetadata', () => {
        if (elements.videoSubTitleOverlay && elements.videoSubTitleOverlay.style.display === 'block') {
            applySubtitleOverlayStyles(elements.videoSubTitleOverlay);
        }
        updateCustomProgress();
    });
    window.addEventListener('resize', () => {
        if (elements.videoSubTitleOverlay && elements.videoSubTitleOverlay.style.display === 'block') {
            applySubtitleOverlayStyles(elements.videoSubTitleOverlay);
        }
        updateCustomProgress();
    });

    // Cập nhật style overlay tức thì khi người dùng đổi cài đặt trên UI
    const styleInputs = [
        elements.subColor, elements.subSize, elements.subBg, elements.subPosition,
        elements.subFont, elements.subBgColor, elements.subBgOpacity,
        elements.subOutline, elements.subOutlineWidth, elements.subShadow
    ];
    styleInputs.forEach(input => {
        if (input) {
            input.addEventListener('change', () => {
                // Reset custom drag margins to position defaults when alignment dropdown changes
                if (input === elements.subPosition) {
                    const val = elements.subPosition.value;
                    if (val === 'center') {
                        configs.sub_margin_v_percent = 50;
                    } else {
                        configs.sub_margin_v_percent = 12;
                    }
                }
                if (elements.videoSubTitleOverlay && elements.videoSubTitleOverlay.style.display === 'block') {
                    applySubtitleOverlayStyles(elements.videoSubTitleOverlay);
                }
            });
            input.addEventListener('input', () => {
                if (elements.videoSubTitleOverlay && elements.videoSubTitleOverlay.style.display === 'block') {
                    applySubtitleOverlayStyles(elements.videoSubTitleOverlay);
                }
            });
        }
    });
}

// ============================================================
// WEBSOCKET & POLLING
// ============================================================

function connectWebSocket(jobId) {
    disconnectWebSocket();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${jobId}`;

    try {
        websocket = new WebSocket(wsUrl);

        websocket.onopen = () => {
            console.log('[WS] Connected');
        };

        websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                jobsCache = data;
                updateUI(data);
            } catch (e) {
                console.error('[WS] Parse error:', e);
            }
        };

        websocket.onclose = () => {
            console.log('[WS] Disconnected');
            if (currentJobId && jobsCache && !['completed', 'error'].includes(jobsCache.status)) {
                reconnectTimer = setTimeout(() => {
                    console.log('[WS] Reconnecting...');
                    connectWebSocket(jobId);
                }, 3000);
            }
        };

        websocket.onerror = (error) => {
            console.error('[WS] Error:', error);
        };

    } catch (e) {
        console.error('[WS] Connection failed:', e);
        startPolling(jobId);
    }
}

function disconnectWebSocket() {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
    if (websocket) {
        websocket.close();
        websocket = null;
    }
}

let pollingInterval = null;
function startPolling(jobId) {
    stopPolling();
    pollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${jobId}`);
            if (response.ok) {
                const data = await response.json();
                jobsCache = data;
                updateUI(data);

                if (['completed', 'error'].includes(data.status)) {
                    stopPolling();
                }
            }
        } catch (e) {
            console.error('[Poll] Error:', e);
        }
    }, 2500);
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// ============================================================
// UI STATE UPDATER
// ============================================================

function updateUI(data) {
    if (!data) return;

    // 1. Cập nhật tiến trình tổng
    const overall = data.overall_progress || 0;
    elements.overallProgressBar.style.width = overall + '%';
    elements.overallPercent.textContent = overall + '%';

    if (data.video_info && data.video_info.title) {
        elements.videoTitle.textContent = data.video_info.title;
        elements.resultTitle.textContent = data.video_info.title;
        
        // Cập nhật Header Workspace Editor
        if (elements.editorVideoTitle) {
            elements.editorVideoTitle.textContent = data.video_info.title;
        }
        
        if (elements.editorVideoMeta) {
            const duration = Math.round(data.video_info.duration) + 's';
            const size = data.video_info.size ? (data.video_info.size / 1024 / 1024).toFixed(1) + ' MB' : '-- MB';
            const res = (data.video_info.width && data.video_info.height) ? `${data.video_info.width}x${data.video_info.height}` : '--';
            elements.editorVideoMeta.textContent = `${duration} · ${size} · ${res} · Xử lý xong`;
        }
    }

    // 2. Cập nhật các step
    if (data.steps) {
        data.steps.forEach((stepData, index) => {
            const stepEl = document.querySelector(`.step[data-step="${index}"]`);
            if (!stepEl) return;
            stepEl.className = `step ${stepData.status}`;
            const fill = stepEl.querySelector('.step-progress-fill');
            if (fill) fill.style.width = stepData.progress + '%';
        });
    }

    // 3. Cập nhật text tiến trình hiện tại
    if (data.current_step >= 0 && data.message) {
        const currentStepEl = document.querySelector(`.step[data-step="${data.current_step}"]`);
        if (currentStepEl) {
            const msg = currentStepEl.querySelector('.step-message');
            if (msg) msg.textContent = data.message;
        }
    }

    // 4. Xử lý trạng thái Job đặc biệt
    if (data.status === 'review') {
        if (data.segments && elements.workspaceTab.classList.contains('hidden')) {
            showTab('workspaceTab');
            
            // Phát video gốc để preview
            elements.workspaceVideo.src = data.video_url;
            
            renderSubtitleList(data.segments);
            setupVideoSync();
            initializeWorkspaceSliders(data);
            
            disconnectWebSocket();
        }
    } else if (data.status === 'completed') {
        showTab('resultTab');
        if (data.download_url) {
            elements.downloadBtn.href = data.download_url;
            if (elements.downloadSrtBtn) {
                const srtUrl = `/api/download/srt/${currentJobId}`;
                elements.downloadSrtBtn.href = srtUrl;
                elements.downloadSrtBtn.style.display = 'inline-flex';
            }
        }
        disconnectWebSocket();
        stopPolling();
    } else if (data.status === 'error') {
        showTab('errorTab');
        elements.errorDetail.textContent = data.error || 'Đã xảy ra lỗi.';
        disconnectWebSocket();
        stopPolling();
    }
}

// ============================================================
// HISTORY TAB LOGIC
// ============================================================

/**
 * Tải danh sách lịch sử dịch thuật từ FastAPI và render ra UI
 */
async function loadHistoryList() {
    elements.historyList.innerHTML = '<div class="empty-history">⏳ Đang tải lịch sử...</div>';

    try {
        // Tải song song cả lịch sử và danh sách thư mục tự tạo sẵn
        const [historyRes, foldersRes] = await Promise.all([
            fetch('/api/history'),
            fetch('/api/folders')
        ]);
        if (!historyRes.ok || !foldersRes.ok) throw new Error('Không thể tải lịch sử hoặc thư mục từ máy chủ.');

        const data = await historyRes.json();
        const folders = await foldersRes.json();
        
        // Cập nhật autocomplete danh sách các bộ/seri phim đã có
        const datalist = document.getElementById('seriesDatalist');
        if (datalist) {
            datalist.innerHTML = folders.map(s => `<option value="${s}"></option>`).join('');
        }
        
        // Cập nhật dropdown chọn thư mục xuất
        populateWorkspaceFolderSelect(folders);
        
        if (data.length === 0 && folders.length === 0) {
            elements.historyList.innerHTML = '<div class="empty-history">Chưa có dự án dịch video hoặc thư mục nào được tạo.</div>';
            return;
        }

        elements.historyList.innerHTML = '';

        // Phân nhóm các job theo tên bộ (series_name)
        const itemsToRender = [];
        const seriesMap = {};

        // Nạp trước các thư mục trống tự tạo vào danh sách render
        folders.forEach(sName => {
            const trimmed = sName.trim();
            if (trimmed && !seriesMap[trimmed]) {
                const seriesObj = {
                    type: 'series',
                    series_name: trimmed,
                    created_at: 0, // Sẽ được cập nhật khi có job thực tế
                    jobs: []
                };
                seriesMap[trimmed] = seriesObj;
                itemsToRender.push(seriesObj);
            }
        });

        // Phân phối các job vào thư mục tương ứng hoặc để ở ngoài
        data.forEach(job => {
            const sName = job.series_name ? job.series_name.trim() : "";
            if (sName) {
                if (!seriesMap[sName]) {
                    const seriesObj = {
                        type: 'series',
                        series_name: sName,
                        created_at: job.created_at,
                        jobs: []
                    };
                    seriesMap[sName] = seriesObj;
                    itemsToRender.push(seriesObj);
                }
                seriesMap[sName].jobs.push(job);
                if (job.created_at > seriesMap[sName].created_at) {
                    seriesMap[sName].created_at = job.created_at;
                }
            } else {
                itemsToRender.push({
                    type: 'standalone',
                    job: job,
                    created_at: job.created_at
                });
            }
        });

        // Render từng item (bộ phim hoặc video riêng lẻ)
        itemsToRender.forEach(itemData => {
            if (itemData.type === 'standalone') {
                const job = itemData.job;
                const item = document.createElement('div');
                item.className = 'history-item';
                
                let statusText = 'Chờ';
                let badgeClass = 'processing';
                
                if (job.status === 'completed') {
                    statusText = 'Đã xử lý';
                    badgeClass = 'completed';
                } else if (job.status === 'review') {
                    statusText = 'Chờ duyệt';
                    badgeClass = 'review';
                } else if (job.status === 'error') {
                    statusText = 'Lỗi';
                    badgeClass = 'error';
                } else if (job.status === 'processing') {
                    statusText = 'Đang xử lý';
                    badgeClass = 'processing';
                }

                const title = job.video_info ? job.video_info.title : 'Video chưa xác định';
                const duration = job.video_info ? `${Math.round(job.video_info.duration)}s` : '--';
                const dateStr = new Date(job.created_at * 1000).toLocaleString('vi-VN');

                item.innerHTML = `
                    <div class="history-thumb">
                        <span class="history-thumb-icon">🎬</span>
                    </div>
                    <div class="history-info">
                        <div class="history-title" title="${title}">${title}</div>
                        <div class="history-meta">
                            <span>⏱️ ${duration}</span>
                            <span>📅 ${dateStr}</span>
                        </div>
                    </div>
                    <div class="history-status">
                        <span class="status-badge ${badgeClass}">${statusText}</span>
                    </div>
                    <div class="history-actions">
                        <button class="btn-open-project" data-id="${job.job_id}">
                            <span>▶ Mở project</span>
                        </button>
                        <button class="btn-delete-project" data-id="${job.job_id}" title="Xoá dự án">
                            <span>🗑️</span>
                        </button>
                    </div>
                `;

                item.querySelector('.btn-open-project').addEventListener('click', () => {
                    openProject(job.job_id);
                });

                item.querySelector('.btn-delete-project').addEventListener('click', () => {
                    if (confirm(`Bạn có chắc chắn muốn xoá vĩnh viễn dự án "${title}"?`)) {
                        deleteProject(job.job_id);
                    }
                });

                elements.historyList.appendChild(item);
            } else {
                // Bộ phim / Series Group
                const seriesItem = document.createElement('div');
                seriesItem.className = 'history-item series-group-item';
                
                const latestDateStr = itemData.created_at > 0 ? new Date(itemData.created_at * 1000).toLocaleString('vi-VN') : '';
                
                let episodesHtml = '';
                itemData.jobs.forEach(job => {
                    let statusText = 'Chờ';
                    let badgeClass = 'processing';
                    
                    if (job.status === 'completed') {
                        statusText = 'Đã xử lý';
                        badgeClass = 'completed';
                    } else if (job.status === 'review') {
                        statusText = 'Chờ duyệt';
                        badgeClass = 'review';
                    } else if (job.status === 'error') {
                        statusText = 'Lỗi';
                        badgeClass = 'error';
                    } else if (job.status === 'processing') {
                        statusText = 'Đang xử lý';
                        badgeClass = 'processing';
                    }

                    const episodeTitle = job.episode_name || (job.video_info ? job.video_info.title : 'Tập chưa đặt tên');
                    const duration = job.video_info ? `${Math.round(job.video_info.duration)}s` : '--';
                    const epDateStr = new Date(job.created_at * 1000).toLocaleString('vi-VN');

                    episodesHtml += `
                        <div class="episode-row">
                            <div class="episode-title" title="${episodeTitle}">${episodeTitle}</div>
                            <div class="episode-meta">
                                <span>⏱️ ${duration}</span>
                                <span>📅 ${epDateStr}</span>
                            </div>
                            <div class="episode-status">
                                <span class="status-badge ${badgeClass}">${statusText}</span>
                            </div>
                            <div class="episode-actions">
                                <button class="btn-open-project mini-btn" data-id="${job.job_id}">
                                    <svg viewBox="0 0 24 24" fill="currentColor" style="width: 10px; height: 10px; margin-right: 4px; display: inline-block; vertical-align: middle;"><path d="M8 5v14l11-7z"/></svg>
                                    <span>Mở project</span>
                                </button>
                                <button class="btn-delete-project mini-btn" data-id="${job.job_id}" title="Xoá tập này">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle;"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                                </button>
                            </div>
                        </div>
                    `;
                });

                let deleteFolderBtnHtml = '';
                let metaInfoHtml = '';
                if (itemData.jobs.length === 0) {
                    metaInfoHtml = `Thư mục trống`;
                    deleteFolderBtnHtml = `
                        <button class="btn-delete-empty-folder" data-name="${itemData.series_name}" title="Xoá thư mục trống" style="margin-top: 10px; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.2); color: #f87171; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 11px; display: inline-flex; align-items: center; gap: 6px; width: fit-content; font-weight: 600; transition: all 0.2s ease;">
                            <span>🗑️ Xóa thư mục</span>
                        </button>
                    `;
                } else {
                    metaInfoHtml = `${itemData.jobs.length} video · ${latestDateStr}`;
                }

                seriesItem.innerHTML = `
                    <div class="series-left-col">
                        <div class="history-thumb series-thumb">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="width: 44px; height: 44px; color: #f59e0b; filter: drop-shadow(0 2px 8px rgba(245, 158, 11, 0.3));">
                                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                            </svg>
                        </div>
                        <div class="series-title-text" title="${itemData.series_name}">${itemData.series_name}</div>
                        <div class="series-meta-info">${metaInfoHtml}</div>
                        ${deleteFolderBtnHtml}
                    </div>
                    <div class="series-right-col">
                        ${episodesHtml || '<div style="color: var(--text-muted); padding: 12px; font-size: 0.85rem; font-style: italic;">Thư mục trống. Thêm video mới từ Trang chủ.</div>'}
                    </div>
                `;

                // Gán sự kiện cho từng tập trong bộ
                seriesItem.querySelectorAll('.episode-row').forEach(row => {
                    const openBtn = row.querySelector('.btn-open-project');
                    const deleteBtn = row.querySelector('.btn-delete-project');
                    const jobId = openBtn.getAttribute('data-id');
                    const epTitle = row.querySelector('.episode-title').textContent;

                    openBtn.addEventListener('click', () => {
                        openProject(jobId);
                    });

                    deleteBtn.addEventListener('click', () => {
                        if (confirm(`Bạn có chắc chắn muốn xoá vĩnh viễn tập "${epTitle}" thuộc bộ "${itemData.series_name}"?`)) {
                            deleteProject(jobId);
                        }
                    });
                });

                // Gán sự kiện cho nút xóa thư mục trống
                const deleteEmptyFolderBtn = seriesItem.querySelector('.btn-delete-empty-folder');
                if (deleteEmptyFolderBtn) {
                    deleteEmptyFolderBtn.addEventListener('click', async () => {
                        if (confirm(`Bạn có chắc chắn muốn xoá thư mục trống "${itemData.series_name}"?`)) {
                            try {
                                const res = await fetch(`/api/folders/${encodeURIComponent(itemData.series_name)}`, { method: 'DELETE' });
                                if (res.ok) {
                                    loadHistoryList();
                                } else {
                                    alert('Không thể xóa thư mục này.');
                                }
                            } catch (err) {
                                alert(`Lỗi: ${err.message}`);
                            }
                        }
                    });
                }

                elements.historyList.appendChild(seriesItem);
            }
        });

    } catch (e) {
        elements.historyList.innerHTML = `<div class="empty-history" style="color: var(--error)">❌ Lỗi: ${e.message}</div>`;
    }
}

/**
 * Mở lại một project cụ thể theo trạng thái hiện tại
 */
async function openProject(jobId) {
    try {
        const response = await fetch(`/api/status/${jobId}`);
        if (!response.ok) throw new Error('Không thể tải thông tin dự án.');

        const data = await response.json();
        currentJobId = jobId;
        jobsCache = data;

        // Reset and load UI dynamically
        if (data.status === 'review') {
            showTab('workspaceTab');
            originalVideoUrl = data.video_url;
            elements.workspaceVideo.src = data.video_url;
            if (elements.workspaceOriginalBtn) {
                elements.workspaceOriginalBtn.style.display = 'none';
            }
            renderSubtitleList(data.segments);
            setupVideoSync();
            initializeWorkspaceSliders(data);
            disconnectWebSocket();

            // Tải danh sách thư mục để populate vào dropdown chọn thư mục xuất
            try {
                const foldersRes = await fetch('/api/folders');
                if (foldersRes.ok) {
                    const folders = await foldersRes.json();
                    populateWorkspaceFolderSelect(folders);
                    
                    // Tự động chọn thư mục hiện tại của dự án nếu có
                    const select = document.getElementById('wsOutputFolderSelect');
                    if (select) {
                        if (data.series_name) {
                            if (Array.from(select.options).some(opt => opt.value === data.series_name)) {
                                select.value = data.series_name;
                            }
                        } else {
                            select.value = 'default';
                        }
                    }
                }
            } catch (e) {
                console.error("Lỗi load folders trong workspace:", e);
            }
            
            // Render video info in Workspace header
            if (data.video_info) {
                elements.editorVideoTitle.textContent = data.video_info.title;
                const duration = Math.round(data.video_info.duration) + 's';
                const size = data.video_info.size ? (data.video_info.size / 1024 / 1024).toFixed(1) + ' MB' : '-- MB';
                const res = (data.video_info.width && data.video_info.height) ? `${data.video_info.width}x${data.video_info.height}` : '--';
                elements.editorVideoMeta.textContent = `${duration} · ${size} · ${res} · Xử lý xong`;
            }
        } else if (data.status === 'completed') {
            showTab('resultTab');
            elements.resultTitle.textContent = data.video_info ? data.video_info.title : '';
            elements.downloadBtn.href = data.download_url;
            if (elements.downloadSrtBtn) {
                const srtUrl = `/api/download/srt/${jobId}`;
                elements.downloadSrtBtn.href = srtUrl;
                elements.downloadSrtBtn.style.display = 'inline-flex';
            }
            disconnectWebSocket();
        } else if (data.status === 'processing') {
            resetProgressSteps();
            elements.progressTitle.textContent = '⚡ Đang tiếp tục xử lý...';
            showTab('progressTab');
            connectWebSocket(jobId);
        } else { // error
            showTab('errorTab');
            elements.errorDetail.textContent = data.error || 'Dự án gặp lỗi.';
            disconnectWebSocket();
        }

    } catch (e) {
        alert(`Không thể mở dự án: ${e.message}`);
    }
}

/**
 * Xoá vĩnh viễn một dự án và các tệp tin lưu trữ
 */
async function deleteProject(jobId) {
    try {
        const response = await fetch(`/api/job/${jobId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Không thể xoá dự án.');

        // Tải lại danh sách lịch sử
        loadHistoryList();

    } catch (e) {
        alert(`Lỗi khi xoá: ${e.message}`);
    }
}

// ============================================================
// ACTION EVENTS
// ============================================================

// Chuyển đổi các Tab trên Sidebar
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        if (item.classList.contains('disabled')) return;

        const tab = item.getAttribute('data-tab');
        if (tab === 'home') {
            showTab('homeTab');
        } else if (tab === 'thumbnail') {
            showTab('thumbnailTab');
        } else if (tab === 'history') {
            showTab('historyTab');
            loadHistoryList();
        } else if (tab === 'srt') {
            showTab('srtTab');
        } else if (tab === 'settings') {
            showTab('settingsTab');
            loadSettingsData();
        } else if (tab === 'editor') {
            if (currentJobId) {
                showTab('workspaceTab');
            } else {
                // Tự động tìm job gần nhất để mở, hoặc báo lỗi
                fetch('/api/history')
                    .then(r => r.json())
                    .then(data => {
                        if (data.length > 0) {
                            openProject(data[0].job_id);
                        } else {
                            alert('Vui lòng tạo dự án mới ở Trang chủ hoặc chọn từ Lịch sử trước.');
                            showTab('homeTab');
                        }
                    }).catch(() => {
                        alert('Vui lòng tạo dự án mới ở Trang chủ hoặc chọn từ Lịch sử trước.');
                        showTab('homeTab');
                    });
            }
        }
    });
});

// Chuyển đổi Tab nhỏ bên trong Workspace
if (elements.tabBtnSubtitles && elements.tabBtnStyling) {
    elements.tabBtnSubtitles.addEventListener('click', () => {
        elements.tabBtnSubtitles.classList.add('active');
        elements.tabBtnStyling.classList.remove('active');
        elements.wsTabSubtitles.classList.remove('hidden');
        elements.wsTabStyling.classList.add('hidden');
    });

    elements.tabBtnStyling.addEventListener('click', () => {
        elements.tabBtnStyling.classList.add('active');
        elements.tabBtnSubtitles.classList.remove('active');
        elements.wsTabStyling.classList.remove('hidden');
        elements.wsTabSubtitles.classList.add('hidden');
    });
}



// Nút bắt đầu dịch thô (Phase 1)
if (elements.processBtn) {
    elements.processBtn.addEventListener('click', async () => {
        const url = elements.urlInput.value.trim();

        // Vô hiệu hóa nút
        elements.processBtn.disabled = true;
        elements.processBtn.querySelector('.btn-text').textContent = 'Đang khởi tạo...';

        const isSeparate = configs.separate_vocals === 'true' || configs.separate_vocals === true;
        const reqData = {
            model_size: configs.model_size,
            source_lang: configs.source_lang,
            original_volume: isSeparate ? 0.8 : 0.15,
            video_quality: configs.video_quality,
            separate_vocals: isSeparate,
            series_name: elements.seriesInput.value.trim() || null,
            episode_name: elements.episodeInput.value.trim() || null,
            context_prompt: document.getElementById('contextInput') ? document.getElementById('contextInput').value.trim() : null
        };

        if (uploadedJobId) {
            reqData.job_id = uploadedJobId;
        } else {
            reqData.url = url;
        }

        try {
            const response = await fetch('/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reqData)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || err.error || 'Lỗi server');
            }

            const data = await response.json();
            currentJobId = data.job_id;

            resetProgressSteps();
            elements.progressTitle.textContent = '⚡ Đang tải video & biên dịch thô';
            showTab('progressTab');

            connectWebSocket(currentJobId);

        } catch (e) {
            showError(`Không thể khởi tạo: ${e.message}`);
            elements.processBtn.disabled = false;
            elements.processBtn.querySelector('.btn-text').textContent = 'Dịch và tạo video';
        }
    });
}

// Nút tạo lồng tiếng và xuất video cuối cùng (Phase 2)
if (elements.exportBtn) {
    elements.exportBtn.addEventListener('click', async () => {
        if (!currentJobId) return;

        elements.exportBtn.disabled = true;
        const btnText = elements.exportBtn.querySelector('.btn-text');
        if (btnText) btnText.textContent = 'Đang xuất...';

        // Dừng video player
        elements.workspaceVideo.pause();

        const subStyle = {
            color: elements.subColor.value,
            size: parseInt(elements.subSize.value),
            bg: elements.subBg.value,
            position: elements.subPosition ? elements.subPosition.value : 'bottom',
            font: elements.subFont ? elements.subFont.value : 'Arial',
            bg_color: elements.subBgColor ? elements.subBgColor.value : '#000000',
            bg_opacity: elements.subBgOpacity ? parseInt(elements.subBgOpacity.value) : 80,
            outline: elements.subOutline ? elements.subOutline.checked : true,
            outline_width: elements.subOutlineWidth ? parseFloat(elements.subOutlineWidth.value) : 4.0,
            shadow: elements.subShadow ? elements.subShadow.checked : false,
            margin_v_percent: configs.sub_margin_v_percent !== undefined ? configs.sub_margin_v_percent : 5
        };

        try {
            const response = await fetch('/api/process/finish', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: currentJobId,
                    segments: currentSegments,
                    voice: elements.workspaceVoiceSelect ? elements.workspaceVoiceSelect.value : configs.voice,
                    voice_speed: elements.workspaceVoiceSpeedSelect ? parseFloat(elements.workspaceVoiceSpeedSelect.value) : configs.voice_speed,
                    sub_style: subStyle,
                    original_volume: elements.wsOriginalVolume ? parseFloat(elements.wsOriginalVolume.value) : 0.15,
                    dubbed_volume: elements.wsDubbedVolume ? parseFloat(elements.wsDubbedVolume.value) : 1.0,
                    separate_vocals: document.getElementById('wsSeparateVocals') ? document.getElementById('wsSeparateVocals').checked : false,
                    output_folder: document.getElementById('wsOutputFolderSelect') ? document.getElementById('wsOutputFolderSelect').value : null,
                    custom_output_dir: document.getElementById('wsCustomOutputDir') ? document.getElementById('wsCustomOutputDir').value.trim() : null,
                    blur_bars: window.blurBars || null,
                    logo_settings: window.currentLogoSettings || null
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || err.error || 'Lỗi xuất video');
            }

            elements.progressTitle.textContent = '🎬 Đang lồng tiếng & kết xuất video cuối cùng';
            showTab('progressTab');

            // Bật lại WebSocket kết nối tới giai đoạn 2
            connectWebSocket(currentJobId);

        } catch (e) {
            alert(`Lỗi: ${e.message}`);
            elements.exportBtn.disabled = false;
            if (btnText) btnText.textContent = 'Xuất Video';
        }
    });
}

// Nút Tạo lại âm thanh (hành động tương tự như xuất nhưng giữ nguyên tiến trình review)
if (elements.editorRegenAudioBtn) {
    elements.editorRegenAudioBtn.addEventListener('click', () => {
        elements.exportBtn.click();
    });
}

// Nút Tải File SRT
if (elements.downloadSrtBtn) {
    elements.downloadSrtBtn.addEventListener('click', () => {
        if (!currentJobId) {
            alert('Chưa chọn dự án');
            return;
        }
        const a = document.createElement('a');
        a.href = `/api/download/srt/${currentJobId}`;
        a.setAttribute('download', '');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
}

// Nút Tải File Thumbnail
if (elements.downloadThumbBtn) {
    elements.downloadThumbBtn.addEventListener('click', () => {
        if (!currentJobId) {
            alert('Chưa chọn dự án');
            return;
        }
        const a = document.createElement('a');
        a.href = `/api/download/thumbnail/${currentJobId}`;
        a.setAttribute('download', '');
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
}

// Nút Upload Ảnh Bìa Gốc để sửa thành Bìa Tiếng Việt
if (elements.uploadThumbBtn && elements.thumbFileInput) {
    elements.uploadThumbBtn.addEventListener('click', () => {
        if (!currentJobId) {
            alert('Chưa chọn dự án');
            return;
        }
        elements.thumbFileInput.click();
    });

    elements.thumbFileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file || !currentJobId) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            if (typeof showToast === 'function') {
                showToast('Đang nạp ảnh bìa gốc & sửa thành Bìa Tiếng Việt...', 'info');
            }
            const res = await fetch(`/api/thumbnail/upload/${currentJobId}`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (res.ok) {
                if (typeof showToast === 'function') {
                    showToast('🎉 Đã tạo Bìa Tiếng Việt thành công!', 'success');
                }
                // Tải luôn file thumbnail vừa sửa về máy
                elements.downloadThumbBtn.click();
            } else {
                alert('Lỗi: ' + (data.error || 'Không thể upload ảnh bìa'));
            }
        } catch (err) {
            alert('Lỗi kết nối upload thumbnail');
        }
    });
}

// Nút Cập nhật Bìa Thumbnail với Tên Mới
if (elements.btnRegenThumbText) {
    elements.btnRegenThumbText.addEventListener('click', async () => {
        if (!currentJobId) {
            alert('Chưa chọn dự án');
            return;
        }
        const customTitle = elements.thumbTitleInput ? elements.thumbTitleInput.value.trim() : '';
        const customEp = elements.thumbEpInput ? elements.thumbEpInput.value.trim() : '';

        try {
            if (typeof showToast === 'function') {
                showToast('Đang vẽ Tên Phim mới lên Bìa Thumbnail...', 'info');
            }
            const res = await fetch('/api/thumbnail/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: currentJobId,
                    timestamp: 3.0,
                    title_text: customTitle,
                    episode_text: customEp,
                    style: 'banner'
                })
            });
            const data = await res.json();
            if (res.ok) {
                if (typeof showToast === 'function') {
                    showToast('🎉 Đã tạo Bìa với tên mới thành công!', 'success');
                }
                // Tự động tải file Thumbnail mới vừa vẽ về máy
                elements.downloadThumbBtn.click();
            } else {
                alert('Lỗi: ' + (data.error || 'Không thể cập nhật thumbnail'));
            }
        } catch (err) {
            alert('Lỗi kết nối tạo thumbnail');
        }
    });
}

// Xử lý Công Cụ Tạo Thumbnail Độc Lập (Tab Tạo Thumbnail)
if (elements.btnGenerateStThumb && elements.stThumbFile) {
    elements.btnGenerateStThumb.addEventListener('click', async () => {
        const file = elements.stThumbFile.files[0];
        if (!file) {
            alert('Vui lòng chọn 1 file ảnh (.jpg/.png) hoặc video (.mp4)');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('title_text', elements.stThumbTitle ? elements.stThumbTitle.value.trim() : '');
        formData.append('episode_text', elements.stThumbEp ? elements.stThumbEp.value.trim() : '');
        formData.append('timestamp', elements.stThumbTime ? (parseFloat(elements.stThumbTime.value) || 3.0) : 3.0);

        try {
            if (typeof showToast === 'function') {
                showToast('Đang tạo & biên tập Bìa Tiếng Việt...', 'info');
            }
            const res = await fetch('/api/thumbnail/standalone', {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Thumbnail_${elements.stThumbTitle ? elements.stThumbTitle.value.trim() : 'Phim'}.jpg`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                if (typeof showToast === 'function') {
                    showToast('🎉 Đã tải Bìa Tiếng Việt thành công!', 'success');
                }
            } else {
                const data = await res.json();
                alert('Lỗi: ' + (data.error || 'Không thể tạo thumbnail'));
            }
        } catch (err) {
            alert('Lỗi kết nối tạo thumbnail độc lập');
        }
    });
}

// Nút xem trước lồng tiếng (Preview)
if (elements.workspacePreviewBtn) {
    elements.workspacePreviewBtn.addEventListener('click', async () => {
        if (!currentJobId) return;

        elements.workspacePreviewBtn.disabled = true;
        const btnText = elements.workspacePreviewBtn.querySelector('span');
        const oldText = btnText ? btnText.textContent : 'Xem trước lồng tiếng';
        if (btnText) btnText.textContent = '⏳ Đang tạo...';

        // Tạm dừng video player
        elements.workspaceVideo.pause();

        try {
            const response = await fetch('/api/process/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: currentJobId,
                    segments: currentSegments,
                    voice: elements.workspaceVoiceSelect ? elements.workspaceVoiceSelect.value : configs.voice,
                    voice_speed: elements.workspaceVoiceSpeedSelect ? parseFloat(elements.workspaceVoiceSpeedSelect.value) : configs.voice_speed,
                    original_volume: elements.wsOriginalVolume ? parseFloat(elements.wsOriginalVolume.value) : 0.15,
                    dubbed_volume: elements.wsDubbedVolume ? parseFloat(elements.wsDubbedVolume.value) : 1.0
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || err.error || 'Lỗi tạo preview');
            }

            const data = await response.json();
            
            // Thay đổi src của video player thành url preview và tải lại
            elements.workspaceVideo.src = data.preview_url;
            elements.workspaceVideo.load();
            elements.workspaceVideo.play().catch(() => {});

            // Hiển thị nút quay lại video gốc
            if (elements.workspaceOriginalBtn) {
                elements.workspaceOriginalBtn.style.display = 'inline-flex';
            }

            if (elements.menuAudioDubbed && elements.menuAudioOriginal) {
                elements.menuAudioDubbed.classList.add('active');
                elements.menuAudioOriginal.classList.remove('active');
            }

            alert('🔊 Đã tạo bản xem trước lồng tiếng thành công! Video đã được lồng tiếng Việt, bạn có thể nhấn phát phát video để nghe thử.');

        } catch (e) {
            alert(`Lỗi xem trước: ${e.message}`);
        } finally {
            elements.workspacePreviewBtn.disabled = false;
            if (btnText) btnText.textContent = oldText;
        }
    });
}

// Nút xem video gốc
if (elements.workspaceOriginalBtn) {
    elements.workspaceOriginalBtn.addEventListener('click', () => {
        if (!originalVideoUrl) return;

        // Tạm dừng video
        elements.workspaceVideo.pause();

        // Chuyển src về bản gốc và chạy lại
        elements.workspaceVideo.src = originalVideoUrl;
        elements.workspaceVideo.load();
        elements.workspaceVideo.play().catch(() => {});

        // Ẩn nút xem video gốc
        elements.workspaceOriginalBtn.style.display = 'none';

        if (elements.menuAudioOriginal && elements.menuAudioDubbed) {
            elements.menuAudioOriginal.classList.add('active');
            elements.menuAudioDubbed.classList.remove('active');
        }

        alert('🔌 Đã chuyển lại trình phát sang video gốc (tiếng Anh).');
    });
}

// Trở lại màn hình chính để tạo job mới
if (elements.newJobBtn) {
    elements.newJobBtn.addEventListener('click', () => {
        currentJobId = null;
        uploadedJobId = null;
        currentSegments = [];
        
        // Reset inputs
        elements.urlInput.value = '';
        elements.fileInput.value = '';
        elements.processBtn.disabled = true;
        elements.workspaceVideo.src = '';
        if (elements.seriesInput) elements.seriesInput.value = '';
        if (elements.episodeInput) elements.episodeInput.value = '';
        
        // Reset drop zone UI
        if (elements.dropZone) {
            elements.dropZone.querySelector('.drop-zone-content').innerHTML = `
                <span class="upload-icon">📤</span>
                <p class="drop-text">Thả tập tin vào đây</p>
                <p class="drop-sub">Hoặc nhấn để chọn video từ máy tính</p>
            `;
        }

        showTab('homeTab');
        resetProgressSteps();
        elements.urlInput.focus();
    });
}

// Chỉnh sửa lại
if (elements.editAgainBtn) {
    elements.editAgainBtn.addEventListener('click', async () => {
        if (!currentJobId || !jobsCache) return;
        const data = jobsCache;
        showTab('workspaceTab');
        originalVideoUrl = data.video_url;
        elements.workspaceVideo.src = data.video_url;
        if (elements.workspaceOriginalBtn) elements.workspaceOriginalBtn.style.display = 'none';
        renderSubtitleList(data.segments);
        setupVideoSync();
        initializeWorkspaceSliders(data);
        disconnectWebSocket();
        try {
            const foldersRes = await fetch('/api/folders');
            if (foldersRes.ok) {
                const folders = await foldersRes.json();
                populateWorkspaceFolderSelect(folders);
                const select = document.getElementById('wsOutputFolderSelect');
                if (select) {
                    if (data.series_name && Array.from(select.options).some(opt => opt.value === data.series_name)) {
                        select.value = data.series_name;
                    } else {
                        select.value = 'default';
                    }
                }
            }
        } catch (e) {}
        if (data.video_info) {
            elements.editorVideoTitle.textContent = data.video_info.title;
            const duration = Math.round(data.video_info.duration) + 's';
            const size = data.video_info.size ? (data.video_info.size / 1024 / 1024).toFixed(1) + ' MB' : '-- MB';
            const res = (data.video_info.width && data.video_info.height) ? `${data.video_info.width}x${data.video_info.height}` : '--';
            elements.editorVideoMeta.textContent = `${duration} • ${size} • ${res} • Đang chỉnh sửa lại`;
        }
    });
}

// Thử lại
if (elements.retryBtn) {
    elements.retryBtn.addEventListener('click', () => {
        elements.newJobBtn.click();
    });
}

// ============================================================
// SRT TO AUDIO HANDLERS
// ============================================================

// Trigger file input khi nhấn Upload SRT hoặc Chọn SRT
if (elements.srtUploadBtn && elements.srtFileInput) {
    elements.srtUploadBtn.addEventListener('click', () => {
        elements.srtFileInput.click();
    });
}
if (elements.srtChooseFileBtn && elements.srtFileInput) {
    elements.srtChooseFileBtn.addEventListener('click', () => {
        elements.srtFileInput.click();
    });
}

// Đọc nội dung file phụ đề khi người dùng chọn
if (elements.srtFileInput) {
    elements.srtFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (elements.srtFileStatusText) {
            elements.srtFileStatusText.value = file.name;
        }

        const reader = new FileReader();
        reader.onload = (event) => {
            if (elements.srtTextArea) {
                elements.srtTextArea.value = event.target.result;
                parseSRTLocal();
            }
        };
        reader.readAsText(file);
    });
}

// Hàm phân tích cấu trúc phụ đề cục bộ để thông báo nhanh
function parseSRTLocal() {
    if (!elements.srtTextArea) return;
    const text = elements.srtTextArea.value.trim();
    
    if (elements.srtParseStatus) {
        elements.srtParseStatus.classList.remove('hidden');
        if (!text) {
            elements.srtParseStatus.innerHTML = '<span style="color: var(--error)">❌ Vui lòng nhập hoặc tải file phụ đề SRT.</span>';
            elements.srtParseStatus.style.background = 'rgba(239, 68, 68, 0.1)';
            return;
        }

        // Cắt theo các khối phụ đề chuẩn
        const normalized = text.replace(/\r\n/g, '\n').trim();
        const blocks = normalized.split('\n\n');
        let validCount = 0;

        blocks.forEach(block => {
            const lines = block.trim().split('\n');
            if (lines.length >= 3 && lines[1].includes('-->')) {
                validCount++;
            }
        });

        if (validCount > 0) {
            elements.srtParseStatus.innerHTML = `<span style="color: var(--success)">✓ Đã phát hiện ${validCount} phân đoạn phụ đề hợp lệ. Sẵn sàng tạo audio!</span>`;
            elements.srtParseStatus.style.background = 'rgba(16, 185, 129, 0.1)';
        } else {
            elements.srtParseStatus.innerHTML = '<span style="color: var(--error)">⚠️ Định dạng không đúng chuẩn SRT. Phải có chỉ số câu và mốc thời gian.</span>';
            elements.srtParseStatus.style.background = 'rgba(239, 68, 68, 0.1)';
        }
    }
}

// Bắt sự kiện click nút Phân tích
if (elements.srtParseBtn) {
    elements.srtParseBtn.addEventListener('click', () => {
        parseSRTLocal();
    });
}

// Điều hướng chọn giới tính giọng đọc (Nam/Nữ)
if (elements.srtGenderMaleBtn && elements.srtGenderFemaleBtn && elements.srtVoiceSelect) {
    elements.srtGenderMaleBtn.addEventListener('click', () => {
        elements.srtGenderMaleBtn.classList.add('active');
        elements.srtGenderFemaleBtn.classList.remove('active');
        
        elements.srtVoiceSelect.innerHTML = `
            <option value="vi-VN-NamMinhNeural" selected>👨 Giọng nam (Nam Minh)</option>
        `;
    });

    elements.srtGenderFemaleBtn.addEventListener('click', () => {
        elements.srtGenderFemaleBtn.classList.add('active');
        elements.srtGenderMaleBtn.classList.remove('active');
        
        elements.srtVoiceSelect.innerHTML = `
            <option value="vi-VN-HoaiMyNeural" selected>👩 Giọng nữ (Hoài My)</option>
        `;
    });
}

// Gửi yêu cầu lồng tiếng sang máy chủ
if (elements.srtGenerateBtn) {
    elements.srtGenerateBtn.addEventListener('click', async () => {
        if (!elements.srtTextArea) return;
        const srtContent = elements.srtTextArea.value.trim();
        if (!srtContent) {
            alert('Vui lòng nhập hoặc tải file phụ đề SRT lên trước!');
            return;
        }

        // Vô hiệu hóa nút trong lúc xử lý
        elements.srtGenerateBtn.disabled = true;
        const btnText = elements.srtGenerateBtn.querySelector('.btn-text');
        if (btnText) btnText.textContent = 'Đang tổng hợp...';

        if (elements.srtResultActionContainer) {
            elements.srtResultActionContainer.classList.add('hidden');
        }

        try {
            const response = await fetch('/api/srt-to-audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    srt_content: srtContent,
                    voice: elements.srtVoiceSelect ? elements.srtVoiceSelect.value : 'vi-VN-NamMinhNeural',
                    voice_speed: 1.0
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || err.error || 'Lỗi xử lý đầu ra từ máy chủ');
            }

            const data = await response.json();
            
            // Cập nhật giao diện kết quả khi thành công
            if (elements.srtOutputFileName) {
                elements.srtOutputFileName.textContent = data.filename;
            }
            if (elements.srtDownloadAudioBtn) {
                elements.srtDownloadAudioBtn.href = data.download_url;
            }
            if (elements.srtResultActionContainer) {
                elements.srtResultActionContainer.classList.remove('hidden');
            }

            alert(`🎉 Đã tạo giọng nói thành công cho ${data.segments_count} đoạn phụ đề!`);

        } catch (e) {
            alert(`Lỗi khi tạo audio lồng tiếng: ${e.message}`);
        } finally {
            elements.srtGenerateBtn.disabled = false;
            if (btnText) btnText.textContent = 'Tạo audio';
        }
    });
}

// ============================================================
// INITIALIZE
// ============================================================

window.addEventListener('load', () => {
    if (elements.urlInput) elements.urlInput.focus();
    
    // Check FFmpeg status
    fetch('/api/health')
        .then(r => r.json())
        .then(data => {
            if (data.ffmpeg !== 'installed') {
                showError('⚠️ Cảnh báo: FFmpeg chưa được cài đặt trên hệ thống! Vui lòng cài đặt FFmpeg.');
            }
        }).catch(() => {});

    // Đồng bộ hiển thị các giá trị sliders và trạng thái checkbox điều khiển của Style panel
    if (elements.subSize) {
        const sizeVal = document.getElementById('subSizeVal');
        const updateSize = () => {
            if (sizeVal) sizeVal.textContent = elements.subSize.value + 'px';
        };
        elements.subSize.addEventListener('input', updateSize);
        updateSize();
    }

    if (elements.subBgOpacity) {
        const bgOpacityVal = document.getElementById('subBgOpacityVal');
        const updateOpacity = () => {
            if (bgOpacityVal) bgOpacityVal.textContent = elements.subBgOpacity.value + '%';
        };
        elements.subBgOpacity.addEventListener('input', updateOpacity);
        updateOpacity();
    }

    if (elements.subOutlineWidth) {
        const outlineWidthVal = document.getElementById('subOutlineWidthVal');
        const updateOutlineWidth = () => {
            if (outlineWidthVal) outlineWidthVal.textContent = elements.subOutlineWidth.value + 'px';
        };
        elements.subOutlineWidth.addEventListener('input', updateOutlineWidth);
        updateOutlineWidth();
    }

    if (elements.subOutline) {
        const thicknessGroup = document.getElementById('outlineThicknessGroup');
        const updateOutlineState = () => {
            if (thicknessGroup) {
                if (elements.subOutline.checked) {
                    thicknessGroup.style.opacity = '1';
                    if (elements.subOutlineWidth) elements.subOutlineWidth.removeAttribute('disabled');
                } else {
                    thicknessGroup.style.opacity = '0.4';
                    if (elements.subOutlineWidth) elements.subOutlineWidth.setAttribute('disabled', 'true');
                }
            }
        };
        elements.subOutline.addEventListener('change', updateOutlineState);
        updateOutlineState();
    }

    if (elements.wsOriginalVolume) {
        const updateOrigVolume = () => {
            if (elements.wsOriginalVolumeVal) {
                elements.wsOriginalVolumeVal.textContent = Math.round(parseFloat(elements.wsOriginalVolume.value) * 100) + '%';
            }
        };
        elements.wsOriginalVolume.addEventListener('input', updateOrigVolume);
        elements.wsOriginalVolume.addEventListener('change', updateOrigVolume);
        updateOrigVolume();
    }

    const wsSeparateVocals = document.getElementById('wsSeparateVocals');
    if (wsSeparateVocals) {
        wsSeparateVocals.addEventListener('change', () => {
            if (elements.wsOriginalVolume) {
                const newVol = wsSeparateVocals.checked ? 0.8 : 0.15;
                elements.wsOriginalVolume.value = newVol;
                if (elements.wsOriginalVolumeVal) {
                    elements.wsOriginalVolumeVal.textContent = Math.round(newVol * 100) + '%';
                }
            }
        });
    }
    const wsOutputFolderSelect = document.getElementById('wsOutputFolderSelect');
    const wsCustomOutputDirGroup = document.getElementById('wsCustomOutputDirGroup');
    if (wsOutputFolderSelect && wsCustomOutputDirGroup) {
        wsOutputFolderSelect.addEventListener('change', () => {
            if (wsOutputFolderSelect.value === 'custom') {
                wsCustomOutputDirGroup.classList.remove('hidden');
            } else {
                wsCustomOutputDirGroup.classList.add('hidden');
            }
        });
    }

    if (elements.wsDubbedVolume) {
        const updateDubVolume = () => {
            if (elements.wsDubbedVolumeVal) {
                elements.wsDubbedVolumeVal.textContent = Math.round(parseFloat(elements.wsDubbedVolume.value) * 100) + '%';
            }
        };
        elements.wsDubbedVolume.addEventListener('input', updateDubVolume);
        elements.wsDubbedVolume.addEventListener('change', updateDubVolume);
        updateDubVolume();
    }

    // Sự kiện nút Tạo thư mục sẵn
    const btnCreateFolder = document.getElementById('btnCreateFolder');
    if (btnCreateFolder) {
        btnCreateFolder.addEventListener('click', async () => {
            const folderName = prompt("Nhập tên thư mục mới cần tạo:");
            if (!folderName) return;
            const trimmed = folderName.trim();
            if (!trimmed) return;
            
            try {
                const res = await fetch('/api/folders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: trimmed })
                });
                if (res.ok) {
                    loadHistoryList();
                    alert(`Đã tạo thư mục "${trimmed}" thành công!`);
                } else {
                    const errData = await res.json();
                    alert(`Lỗi: ${errData.error || 'Không thể tạo thư mục.'}`);
                }
            } catch (err) {
                alert(`Lỗi kết nối: ${err.message}`);
            }
        });
    }

    // Sự kiện nút Nghe thử giọng đọc ở Trang chủ
    const btnPreviewVoiceHome = document.getElementById('btnPreviewVoiceHome');
    if (btnPreviewVoiceHome) {
        btnPreviewVoiceHome.addEventListener('click', () => {
            const activeVoiceBtn = document.querySelector('.config-options[data-config="voice"] .option-btn.active');
            const selectedVoice = activeVoiceBtn ? activeVoiceBtn.getAttribute('data-value') : 'vi-VN-HoaiMyNeural';
            playVoicePreview(selectedVoice, btnPreviewVoiceHome);
        });
    }

    // Sự kiện nút Nghe thử giọng đọc ở Workspace Trình chỉnh sửa
    const btnPreviewVoiceWorkspace = document.getElementById('btnPreviewVoiceWorkspace');
    if (btnPreviewVoiceWorkspace) {
        btnPreviewVoiceWorkspace.addEventListener('click', () => {
            const workspaceVoiceSelect = document.getElementById('workspaceVoiceSelect');
            const selectedVoice = workspaceVoiceSelect ? workspaceVoiceSelect.value : 'vi-VN-HoaiMyNeural';
            playVoicePreview(selectedVoice, btnPreviewVoiceWorkspace);
        });
    }
});

let currentPreviewAudio = null;

async function playVoicePreview(voice, btnEl) {
    if (voice === 'none') {
        alert('Tùy chọn này không lồng tiếng, nên không thể nghe thử.');
        return;
    }
    
    // Dừng âm thanh nghe thử trước đó nếu đang phát
    if (currentPreviewAudio) {
        currentPreviewAudio.pause();
        currentPreviewAudio = null;
    }
    
    const originalText = btnEl.innerHTML;
    btnEl.setAttribute('disabled', 'true');
    btnEl.innerHTML = '<span>⏳ Đang tải...</span>';
    
    try {
        const response = await fetch(`/api/voice-preview?voice=${encodeURIComponent(voice)}`);
        if (!response.ok) throw new Error('Không thể tải giọng đọc thử.');
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        currentPreviewAudio = new Audio(url);
        currentPreviewAudio.onended = () => {
            btnEl.removeAttribute('disabled');
            btnEl.innerHTML = originalText;
        };
        currentPreviewAudio.onerror = () => {
            btnEl.removeAttribute('disabled');
            btnEl.innerHTML = originalText;
            alert('Lỗi khi phát âm thanh nghe thử.');
        };
        await currentPreviewAudio.play();
        btnEl.innerHTML = '<span>🔊 Đang phát...</span>';
    } catch (err) {
        btnEl.removeAttribute('disabled');
        btnEl.innerHTML = originalText;
        alert(`Lỗi nghe thử giọng đọc: ${err.message}`);
    }
}

window.addEventListener('beforeunload', () => {
    disconnectWebSocket();
    stopPolling();
});


// ============================================================
// SETTINGS PAGE FUNCTIONS
// ============================================================

async function loadSettingsData() {
    try {
        const res = await fetch('/api/settings');
        const data = await res.json();

        // API Keys (masked values)
        const keyMap = {
            gemini: 'keyGemini',
            groq: 'keyGroq',
            github: 'keyGithub',
            sambanova: 'keySambanova',
            elevenlabs: 'keyElevenlabs',
        };
        const statusMap = {
            gemini: 'statusGemini',
            groq: 'statusGroq',
            github: 'statusGithub',
            sambanova: 'statusSambanova',
            elevenlabs: 'statusElevenlabs',
        };

        for (const [key, inputId] of Object.entries(keyMap)) {
            const inputEl = document.getElementById(inputId);
            if (key === 'gemini') {
                const container = document.getElementById('geminiKeysContainer');
                if (container) container.innerHTML = '';
                if (data.api_keys[key]) {
                    const keys = data.api_keys[key].split(',');
                    for (let i = 0; i < keys.length; i++) {
                        addGeminiKeyInput(keys[i]?.trim());
                    }
                    if (keys.length === 0) addGeminiKeyInput('');
                } else {
                    addGeminiKeyInput('');
                }
            } else if (data.api_keys[key]) {
                if (inputEl) {
                    inputEl.value = data.api_keys[key];
                }
            }
            const statusEl = document.getElementById(statusMap[key]);
            if (statusEl) {
                if (data.api_status[key]) {
                    statusEl.textContent = '✅ Đã cấu hình';
                    statusEl.className = 'api-status status-ok';
                } else {
                    statusEl.textContent = '⚠️ Chưa cấu hình';
                    statusEl.className = 'api-status status-missing';
                }
            }
        }

        // Directories
        const dirDl = document.getElementById('dirDownloads');
        const dirOut = document.getElementById('dirOutputs');
        const dirTmp = document.getElementById('dirTemp');
        if (dirDl) dirDl.value = data.directories.downloads || '';
        if (dirOut) dirOut.value = data.directories.outputs || '';
        if (dirTmp) dirTmp.value = data.directories.temp || '';

        // Voices
        const vf = document.getElementById('voiceFemale');
        const vm = document.getElementById('voiceMale');
        if (vf) vf.value = data.voices.default_female || 'vi-VN-HoaiMyNeural';
        if (vm) vm.value = data.voices.default_male || 'vi-VN-NamMinhNeural';

        // Audio volumes
        const volOrig = document.getElementById('volOriginal');
        const volDub = document.getElementById('volDubbed');
        const volOrigVal = document.getElementById('volOriginalVal');
        const volDubVal = document.getElementById('volDubbedVal');
        if (volOrig) {
            volOrig.value = Math.round((data.audio.original_volume || 0.15) * 100);
            if (volOrigVal) volOrigVal.textContent = volOrig.value + '%';
        }
        if (volDub) {
            volDub.value = Math.round((data.audio.dubbed_volume || 1.0) * 100);
            if (volDubVal) volDubVal.textContent = volDub.value + '%';
        }

        // System info
        const si = data.system_info;
        const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setVal('sysFFmpeg', si.ffmpeg ? '✅ Đã cài đặt' : '❌ Chưa cài đặt');
        setVal('sysGPU', si.gpu_cuda ? '✅ NVIDIA GPU' : '⚠️ Không có (CPU)');
        setVal('sysWhisperDev', si.whisper_device);
        setVal('sysWhisperComp', si.whisper_compute_type);
        setVal('sysDlSize', si.downloads_size);
        setVal('sysOutSize', si.outputs_size);
        setVal('sysTmpSize', si.temp_size);
        setVal('sysVersion', 'v' + si.version);

    } catch (err) {
        console.error('[Settings] Lỗi tải cấu hình:', err);
    }
}

// Toggle hiện / ẩn API Key
function toggleKeyVis(inputId, btn) {
    const inp = document.getElementById(inputId);
    if (!inp) return;
    if (inp.type === 'password') {
        inp.type = 'text';
        btn.textContent = '🔒';
    } else {
        inp.type = 'password';
        btn.textContent = '👁️';
    }
}

// Volume slider realtime display
document.addEventListener('DOMContentLoaded', () => {
    const volOrig = document.getElementById('volOriginal');
    const volDub = document.getElementById('volDubbed');
    const volOrigVal = document.getElementById('volOriginalVal');
    const volDubVal = document.getElementById('volDubbedVal');
    if (volOrig && volOrigVal) {
        volOrig.addEventListener('input', () => { volOrigVal.textContent = volOrig.value + '%'; });
    }
    if (volDub && volDubVal) {
        volDub.addEventListener('input', () => { volDubVal.textContent = volDub.value + '%'; });
    }

    // Save settings button
    const btnSave = document.getElementById('btnSaveSettings');
    if (btnSave) {
        btnSave.addEventListener('click', saveSettingsData);
    }
});

async function saveSettingsData() {
    const btn = document.getElementById('btnSaveSettings');
    const origText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Đang lưu...</span>';
        btn.disabled = true;
    }

    try {
        const geminiInputs = document.querySelectorAll('.gemini-dynamic-input');
        const geminiKeys = Array.from(geminiInputs).map(i => i.value.trim()).filter(Boolean).join(',');

        const payload = {
            api_keys: {
                gemini: geminiKeys,
                groq: document.getElementById('keyGroq')?.value || '',
                github: document.getElementById('keyGithub')?.value || '',
                sambanova: document.getElementById('keySambanova')?.value || '',
                elevenlabs: document.getElementById('keyElevenlabs')?.value || '',
            },
            directories: {
                downloads: document.getElementById('dirDownloads')?.value || '',
                outputs: document.getElementById('dirOutputs')?.value || '',
                temp: document.getElementById('dirTemp')?.value || '',
            },
            voices: {
                default_female: document.getElementById('voiceFemale')?.value || '',
                default_male: document.getElementById('voiceMale')?.value || '',
            },
            audio: {
                original_volume: (parseInt(document.getElementById('volOriginal')?.value || '15')) / 100,
                dubbed_volume: (parseInt(document.getElementById('volDubbed')?.value || '100')) / 100,
            },
        };

        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const result = await res.json();

        if (btn) {
            btn.innerHTML = '<span class="btn-icon">✅</span><span class="btn-text">Đã lưu thành công!</span>';
            setTimeout(() => {
                btn.innerHTML = origText;
                btn.disabled = false;
            }, 2000);
        }

        // Reload data to refresh status badges
        await loadSettingsData();

    } catch (err) {
        if (btn) {
            btn.innerHTML = origText;
            btn.disabled = false;
        }
        alert('Lỗi lưu cài đặt: ' + err.message);
    }
}

async function doCleanup(target) {
    const names = {
        temp: 'thư mục tạm (Temp)',
        history: 'toàn bộ lịch sử dự án',
        downloads: 'tất cả video đã tải về',
    };
    const confirmed = confirm(`⚠️ Bạn có chắc chắn muốn xóa ${names[target] || target}?\n\nHành động này không thể hoàn tác!`);
    if (!confirmed) return;

    try {
        const res = await fetch('/api/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target }),
        });
        const result = await res.json();
        alert('✅ ' + result.message);

        // Reload settings to update disk usage
        await loadSettingsData();
    } catch (err) {
        alert('Lỗi dọn dẹp: ' + err.message);
    }
}


// ==========================================
// THÊM LOGIC CHO TÍNH NĂNG LOGO / WATERMARK
// ==========================================
window.currentLogoSettings = {
    visible: true,
    size: 15,
    opacity: 100,
    x: 0.05, // 5% from left
    y: 0.05, // 5% from top
    base64: null,
    file: null
};

document.addEventListener('DOMContentLoaded', () => {
    const logoUploadInput = document.getElementById('logoUploadInput');
    const logoSettingsGroup = document.getElementById('logoSettingsGroup');
    const logoVisibleToggle = document.getElementById('logoVisibleToggle');
    const logoSizeSlider = document.getElementById('logoSizeSlider');
    const logoSizeVal = document.getElementById('logoSizeVal');
    const logoOpacitySlider = document.getElementById('logoOpacitySlider');
    const logoOpacityVal = document.getElementById('logoOpacityVal');
    const removeLogoBtn = document.getElementById('removeLogoBtn');
    const videoLogoOverlay = document.getElementById('videoLogoOverlay');
    const workspaceVideo = document.getElementById('workspaceVideo');

    function getVideoActiveArea() {
        const container = workspaceVideo.parentElement;
        if (!workspaceVideo.videoWidth) {
            return { x: 0, y: 0, w: container.clientWidth, h: container.clientHeight };
        }
        const videoRatio = workspaceVideo.videoWidth / workspaceVideo.videoHeight;
        const containerRatio = container.clientWidth / container.clientHeight;
        let actualWidth, actualHeight, xOffset, yOffset;

        if (videoRatio > containerRatio) {
            actualWidth = container.clientWidth;
            actualHeight = actualWidth / videoRatio;
            xOffset = 0;
            yOffset = (container.clientHeight - actualHeight) / 2;
        } else {
            actualHeight = container.clientHeight;
            actualWidth = actualHeight * videoRatio;
            yOffset = 0;
            xOffset = (container.clientWidth - actualWidth) / 2;
        }
        return { x: xOffset, y: yOffset, w: actualWidth, h: actualHeight };
    }

    function clamp(val, min, max) {
        return Math.max(min, Math.min(max, val));
    }

    function updateLogoDisplay() {
        if (!window.currentLogoSettings.file || !window.currentLogoSettings.visible) {
            videoLogoOverlay.style.display = 'none';
            return;
        }
        videoLogoOverlay.style.display = 'block';
        videoLogoOverlay.style.opacity = window.currentLogoSettings.opacity / 100;
        
        const area = getVideoActiveArea();
        
        // Cập nhật width
        const logoW = area.w * (window.currentLogoSettings.size / 100);
        videoLogoOverlay.style.width = logoW + 'px';
        
        // Lấy height thực tế sau khi set width (để clamp Y)
        const logoH = videoLogoOverlay.getBoundingClientRect().height || (logoW); // fallback

        // Đảm bảo x, y nằm trong giới hạn (0.0 -> 1.0)
        let maxX = 1.0 - (logoW / area.w);
        let maxY = 1.0 - (logoH / area.h);
        if (maxX < 0) maxX = 0;
        if (maxY < 0) maxY = 0;

        window.currentLogoSettings.x = clamp(window.currentLogoSettings.x, 0, maxX);
        window.currentLogoSettings.y = clamp(window.currentLogoSettings.y, 0, maxY);

        // Tính pixel
        const pxX = area.x + (window.currentLogoSettings.x * area.w);
        const pxY = area.y + (window.currentLogoSettings.y * area.h);

        videoLogoOverlay.style.left = pxX + 'px';
        videoLogoOverlay.style.top = pxY + 'px';
    }

    // Xử lý Upload
    logoUploadInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            window.currentLogoSettings.file = file.name;
            window.currentLogoSettings.base64 = event.target.result;
            videoLogoOverlay.src = event.target.result;
            logoSettingsGroup.classList.remove('hidden');
            updateLogoDisplay();
            
            // Re-update sau khi ảnh load xong để có height chính xác
            videoLogoOverlay.onload = updateLogoDisplay;
        };
        reader.readAsDataURL(file);
    });

    // Toggle Visible
    logoVisibleToggle.addEventListener('change', (e) => {
        window.currentLogoSettings.visible = e.target.checked;
        updateLogoDisplay();
    });

    // Slider Size
    logoSizeSlider.addEventListener('input', (e) => {
        logoSizeVal.textContent = e.target.value + '%';
        window.currentLogoSettings.size = parseFloat(e.target.value);
        updateLogoDisplay();
    });

    // Slider Opacity
    logoOpacitySlider.addEventListener('input', (e) => {
        logoOpacityVal.textContent = e.target.value + '%';
        window.currentLogoSettings.opacity = parseFloat(e.target.value);
        updateLogoDisplay();
    });

    // Remove Logo
    removeLogoBtn.addEventListener('click', () => {
        window.currentLogoSettings = { visible: true, size: 15, opacity: 100, x: 0.05, y: 0.05, base64: null, file: null };
        logoUploadInput.value = '';
        videoLogoOverlay.src = '';
        logoSettingsGroup.classList.add('hidden');
        updateLogoDisplay();
    });

    // Resize video listener
    window.addEventListener('resize', updateLogoDisplay);
    workspaceVideo.addEventListener('loadedmetadata', updateLogoDisplay);

    // Kéo thả (Drag & Drop)
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let initialSettingX = 0;
    let initialSettingY = 0;

    videoLogoOverlay.addEventListener('mousedown', dragStart);
    videoLogoOverlay.addEventListener('touchstart', dragStart, {passive: false});

    function dragStart(e) {
        if (!window.currentLogoSettings.file || !window.currentLogoSettings.visible) return;
        e.preventDefault();
        isDragging = true;
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        dragStartX = clientX;
        dragStartY = clientY;
        initialSettingX = window.currentLogoSettings.x;
        initialSettingY = window.currentLogoSettings.y;
        videoLogoOverlay.style.border = '2px dashed #8b5cf6'; // Highlight khi drag
        
        document.addEventListener('mousemove', dragMove);
        document.addEventListener('touchmove', dragMove, {passive: false});
        document.addEventListener('mouseup', dragEnd);
        document.addEventListener('touchend', dragEnd);
    }

    function dragMove(e) {
        if (!isDragging) return;
        e.preventDefault();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        
        const deltaX = clientX - dragStartX;
        const deltaY = clientY - dragStartY;
        
        const area = getVideoActiveArea();
        
        // Tính % dịch chuyển
        const deltaPctX = deltaX / area.w;
        const deltaPctY = deltaY / area.h;
        
        window.currentLogoSettings.x = initialSettingX + deltaPctX;
        window.currentLogoSettings.y = initialSettingY + deltaPctY;
        
        updateLogoDisplay();
    }

    function dragEnd(e) {
        if (!isDragging) return;
        isDragging = false;
        videoLogoOverlay.style.border = '2px dashed transparent';
        
        document.removeEventListener('mousemove', dragMove);
        document.removeEventListener('touchmove', dragMove);
        document.removeEventListener('mouseup', dragEnd);
        document.removeEventListener('touchend', dragEnd);

        console.log(`[Logo] Cập nhật tọa độ: X=${(window.currentLogoSettings.x*100).toFixed(2)}%, Y=${(window.currentLogoSettings.y*100).toFixed(2)}%, Kích thước=${window.currentLogoSettings.size}%`);
    }
});

// ==========================================
// THÊM LOGIC CHO TÍNH NĂNG NHIỀU THANH LÀM MỜ (MULTIPLE BLUR BARS)
// ==========================================
window.blurBars = [];

document.addEventListener('DOMContentLoaded', () => {
    const blurBarsContainer = document.getElementById('blurBarsContainer');
    const addBlurBarBtn = document.getElementById('addBlurBarBtn');
    const workspaceVideo = document.getElementById('workspaceVideo');
    const previewContainer = document.querySelector('.preview-container');

    function getVideoActiveArea() {
        const container = workspaceVideo.parentElement;
        if (!workspaceVideo.videoWidth) {
            return { x: 0, y: 0, w: container.clientWidth, h: container.clientHeight };
        }
        const videoRatio = workspaceVideo.videoWidth / workspaceVideo.videoHeight;
        const containerRatio = container.clientWidth / container.clientHeight;
        let actualWidth, actualHeight, xOffset, yOffset;

        if (videoRatio > containerRatio) {
            actualWidth = container.clientWidth;
            actualHeight = actualWidth / videoRatio;
            xOffset = 0;
            yOffset = (container.clientHeight - actualHeight) / 2;
        } else {
            actualHeight = container.clientHeight;
            actualWidth = actualHeight * videoRatio;
            yOffset = 0;
            xOffset = (container.clientWidth - actualWidth) / 2;
        }
        return { x: xOffset, y: yOffset, w: actualWidth, h: actualHeight };
    }

    function renderBlurBarsUI() {
        if (!blurBarsContainer) return;
        blurBarsContainer.innerHTML = '';
        window.blurBars.forEach((bar, index) => {
            const barHTML = `
                <div class="blur-bar-settings-card" style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; border-radius: var(--radius-sm);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-weight: 600; font-size: 0.85rem; display: flex; align-items: center; gap: 8px;">
                            <label class="ui-switch" style="transform: scale(0.8); margin: 0;">
                                <input type="checkbox" class="blur-bar-enable-toggle" data-index="${index}" ${bar.enabled ? 'checked' : ''}>
                                <span class="slider-round"></span>
                            </label>
                            Thanh #${index + 1}
                        </div>
                        <button class="remove-blur-bar-btn" data-index="${index}" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: var(--error); cursor: pointer; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;">Xóa</button>
                    </div>
                    <div class="stylist-group">
                        <div class="label-with-value">
                            <label>VỊ TRÍ DỌC (Y)</label>
                            <span id="blurBarYVal_${index}">${bar.y_percent !== undefined ? bar.y_percent : 85}%</span>
                        </div>
                        <input type="range" class="custom-slider blur-bar-y-slider" data-index="${index}" min="0" max="100" step="1" value="${bar.y_percent !== undefined ? bar.y_percent : 85}">
                    </div>
                    <div class="stylist-group" style="margin-top: 10px;">
                        <div class="label-with-value">
                            <label>VỊ TRÍ NGANG (X)</label>
                            <span id="blurBarXVal_${index}">${bar.x_percent !== undefined ? bar.x_percent : 0}%</span>
                        </div>
                        <input type="range" class="custom-slider blur-bar-x-slider" data-index="${index}" min="0" max="100" step="1" value="${bar.x_percent !== undefined ? bar.x_percent : 0}">
                    </div>
                    <div class="stylist-group" style="margin-top: 10px;">
                        <div class="label-with-value">
                            <label>CHIỀU CAO</label>
                            <span id="blurBarHVal_${index}">${bar.h_percent !== undefined ? bar.h_percent : 15}%</span>
                        </div>
                        <input type="range" class="custom-slider blur-bar-h-slider" data-index="${index}" min="5" max="100" step="1" value="${bar.h_percent !== undefined ? bar.h_percent : 15}">
                    </div>
                    <div class="stylist-group" style="margin-top: 10px;">
                        <div class="label-with-value">
                            <label>CHIỀU RỘNG</label>
                            <span id="blurBarWVal_${index}">${bar.w_percent !== undefined ? bar.w_percent : 100}%</span>
                        </div>
                        <input type="range" class="custom-slider blur-bar-w-slider" data-index="${index}" min="5" max="100" step="1" value="${bar.w_percent !== undefined ? bar.w_percent : 100}">
                    </div>
                    <div class="stylist-group" style="margin-top: 10px;">
                        <div class="label-with-value">
                            <label>CƯỜNG ĐỘ</label>
                            <span id="blurBarIntensityVal_${index}">${bar.intensity}</span>
                        </div>
                        <input type="range" class="custom-slider blur-bar-intensity-slider" data-index="${index}" min="1" max="50" step="1" value="${bar.intensity}">
                    </div>
                </div>
            `;
            blurBarsContainer.insertAdjacentHTML('beforeend', barHTML);
        });

        document.querySelectorAll('.remove-blur-bar-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                window.blurBars.splice(index, 1);
                renderBlurBarsUI();
                updateBlurBarDisplay();
            });
        });

        document.querySelectorAll('.blur-bar-enable-toggle').forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                window.blurBars[index].enabled = e.target.checked;
                updateBlurBarDisplay();
            });
        });

        document.querySelectorAll('.blur-bar-y-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                window.blurBars[index].y_percent = parseFloat(e.target.value);
                const valEl = document.getElementById(`blurBarYVal_${index}`);
                if (valEl) valEl.textContent = e.target.value + '%';
                updateBlurBarDisplay();
            });
        });

        document.querySelectorAll('.blur-bar-x-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                window.blurBars[index].x_percent = parseFloat(e.target.value);
                const valEl = document.getElementById(`blurBarXVal_${index}`);
                if (valEl) valEl.textContent = e.target.value + '%';
                updateBlurBarDisplay();
            });
        });

        document.querySelectorAll('.blur-bar-h-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                window.blurBars[index].h_percent = parseFloat(e.target.value);
                const valEl = document.getElementById(`blurBarHVal_${index}`);
                if (valEl) valEl.textContent = e.target.value + '%';
                updateBlurBarDisplay();
            });
        });

        document.querySelectorAll('.blur-bar-w-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                window.blurBars[index].w_percent = parseFloat(e.target.value);
                const valEl = document.getElementById(`blurBarWVal_${index}`);
                if (valEl) valEl.textContent = e.target.value + '%';
                updateBlurBarDisplay();
            });
        });

        document.querySelectorAll('.blur-bar-intensity-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const index = parseInt(e.target.getAttribute('data-index'));
                window.blurBars[index].intensity = parseInt(e.target.value);
                const valEl = document.getElementById(`blurBarIntensityVal_${index}`);
                if (valEl) valEl.textContent = e.target.value;
                updateBlurBarDisplay();
            });
        });
    }

    function updateBlurBarDisplay() {
        document.querySelectorAll('.blur-bar-overlay-dynamic').forEach(el => el.remove());

        const area = getVideoActiveArea();
        if (!area || area.w === 0) return;

        window.blurBars.forEach((bar, index) => {
            if (!bar.enabled) return;
            
            const overlay = document.createElement('div');
            overlay.className = 'blur-bar-overlay-dynamic';
            overlay.setAttribute('data-index', index);
            
            const yPct = bar.y_percent !== undefined ? bar.y_percent : 85;
            const xPct = bar.x_percent !== undefined ? bar.x_percent : 0;
            const hPct = bar.h_percent !== undefined ? bar.h_percent : 15;
            const wPct = bar.w_percent !== undefined ? bar.w_percent : 100;
            
            const topPx = area.y + (yPct / 100) * area.h;
            const leftPx = area.x + (xPct / 100) * area.w;
            const heightPx = (hPct / 100) * area.h;
            const widthPx = (wPct / 100) * area.w;
            const blurPx = Math.max(2, bar.intensity / 2);

            overlay.style.position = 'absolute';
            overlay.style.zIndex = '5';
            overlay.style.background = 'rgba(0,0,0,0.5)';
            overlay.style.backdropFilter = `blur(${blurPx}px)`;
            overlay.style.boxSizing = 'border-box';
            overlay.style.border = '1px dashed #ef4444';
            overlay.style.cursor = 'move';
            
            overlay.style.top = topPx + 'px';
            overlay.style.left = leftPx + 'px';
            overlay.style.height = heightPx + 'px';
            overlay.style.width = widthPx + 'px';

            if (previewContainer) {
                previewContainer.appendChild(overlay);
            }
        });
    }

    if (addBlurBarBtn) {
        addBlurBarBtn.addEventListener('click', () => {
            window.blurBars.push({
                enabled: true,
                x_percent: 0,
                y_percent: 85,
                w_percent: 100,
                h_percent: 15,
                intensity: 15
            });
            renderBlurBarsUI();
            updateBlurBarDisplay();
        });
    }

    renderBlurBarsUI();
    updateBlurBarDisplay();

    let isDraggingBlurBar = false;
    let draggingBlurBarIndex = -1;
    let blurBarStartY = 0;
    let blurBarStartX = 0;
    let blurBarStartYPercent = 0;
    let blurBarStartXPercent = 0;

    if (previewContainer) {
        previewContainer.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('blur-bar-overlay-dynamic')) {
                isDraggingBlurBar = true;
                draggingBlurBarIndex = parseInt(e.target.getAttribute('data-index'));
                blurBarStartY = e.clientY;
                blurBarStartX = e.clientX;
                blurBarStartYPercent = window.blurBars[draggingBlurBarIndex].y_percent !== undefined ? window.blurBars[draggingBlurBarIndex].y_percent : 85;
                blurBarStartXPercent = window.blurBars[draggingBlurBarIndex].x_percent !== undefined ? window.blurBars[draggingBlurBarIndex].x_percent : 0;
                document.body.style.cursor = 'move';
                e.preventDefault();
            }
        });
    }

    window.addEventListener('mousemove', (e) => {
        if (!isDraggingBlurBar || draggingBlurBarIndex < 0) return;
        const area = getVideoActiveArea();
        if (!area || area.w === 0 || area.h === 0) return;

        const deltaY = e.clientY - blurBarStartY;
        const deltaX = e.clientX - blurBarStartX;
        
        const deltaYPercent = (deltaY / area.h) * 100;
        const deltaXPercent = (deltaX / area.w) * 100;
        
        let newYPercent = blurBarStartYPercent + deltaYPercent;
        let newXPercent = blurBarStartXPercent + deltaXPercent;
        
        const bar = window.blurBars[draggingBlurBarIndex];
        const hPct = bar.h_percent !== undefined ? bar.h_percent : 15;
        const wPct = bar.w_percent !== undefined ? bar.w_percent : 100;

        if (newYPercent < 0) newYPercent = 0;
        if (newYPercent + hPct > 100) newYPercent = 100 - hPct;
        
        if (newXPercent < 0) newXPercent = 0;
        if (newXPercent + wPct > 100) newXPercent = 100 - wPct;

        bar.y_percent = newYPercent;
        bar.x_percent = newXPercent;
        
        const ySlider = document.querySelector(`.blur-bar-y-slider[data-index="${draggingBlurBarIndex}"]`);
        const yVal = document.getElementById(`blurBarYVal_${draggingBlurBarIndex}`);
        if (ySlider) ySlider.value = newYPercent;
        if (yVal) yVal.textContent = Math.round(newYPercent) + '%';
        
        const xSlider = document.querySelector(`.blur-bar-x-slider[data-index="${draggingBlurBarIndex}"]`);
        const xVal = document.getElementById(`blurBarXVal_${draggingBlurBarIndex}`);
        if (xSlider) xSlider.value = newXPercent;
        if (xVal) xVal.textContent = Math.round(newXPercent) + '%';
        
        updateBlurBarDisplay();
    });

    window.addEventListener('mouseup', () => {
        if (isDraggingBlurBar) {
            isDraggingBlurBar = false;
            draggingBlurBarIndex = -1;
            document.body.style.cursor = '';
        }
    });

    window.addEventListener('resize', updateBlurBarDisplay);
    if (workspaceVideo) {
        workspaceVideo.addEventListener('loadedmetadata', updateBlurBarDisplay);
    }
});

let geminiKeyCount = 0;
function addGeminiKeyInput(val = '') {
    geminiKeyCount++;
    const container = document.getElementById('geminiKeysContainer');
    if (!container) return;
    
    const div = document.createElement('div');
    div.className = 'api-key-input-group';
    div.style.marginTop = geminiKeyCount > 1 ? '5px' : '0';
    
    const inputId = 'keyGemini_' + geminiKeyCount;
    
    const input = document.createElement('input');
    input.type = 'password';
    input.id = inputId;
    input.className = 'gemini-dynamic-input';
    input.placeholder = `Dán API Key Gemini...`;
    input.value = val;
    input.style.flex = '1';
    
    const eyeBtn = document.createElement('button');
    eyeBtn.type = 'button';
    eyeBtn.className = 'btn-toggle-eye';
    eyeBtn.innerHTML = '👁️';
    eyeBtn.onclick = function() { toggleKeyVis(inputId, this); };
    
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn-api-remove';
    removeBtn.innerHTML = '✕';
    removeBtn.onclick = function() { div.remove(); };
    removeBtn.title = "Xóa Key này";
    removeBtn.style.background = 'transparent';
    removeBtn.style.border = 'none';
    removeBtn.style.color = '#ff4a4a';
    removeBtn.style.cursor = 'pointer';
    removeBtn.style.padding = '0 5px';
    
    div.appendChild(input);
    div.appendChild(eyeBtn);
    div.appendChild(removeBtn);
    
    container.appendChild(div);
}
