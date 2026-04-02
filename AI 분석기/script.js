document.addEventListener('DOMContentLoaded', () => {
    // Stage Elements
    const mainUi = document.getElementById('main-ui');
    const scannerUi = document.getElementById('scanner-ui');
    const mockAdModal = document.getElementById('mock-ad-modal');
    const resultUi = document.getElementById('result-ui');
    
    // Interactions
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const thumbnailListUi = document.getElementById('thumbnail-list');
    const uploadContentUi = document.getElementById('upload-content');
    const analyzeBtn = document.getElementById('analyze-btn');
    const captureBtn = document.getElementById('capture-btn');
    const retryBtn = document.getElementById('retry-btn');
    const closeAdBtn = document.getElementById('close-ad-btn');
    
    // Sounds
    const tickSound = document.getElementById('tick-sound');
    const boomSound = document.getElementById('boom-sound');
    tickSound.volume = 0.6;
    boomSound.volume = 0.8;

    let selectedFiles = []; // array of { file, dataUrl }
    let analysisResult = null; 
    let statusInterval;

    // File Upload Handlers
    dropZone.addEventListener('click', (e) => {
        // Prevent click if targeting remove button
        if(e.target.classList.contains('remove-thumb-btn')) return;
        fileInput.click();
    });
    
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.transform = 'scale(1.3) rotate(15deg)'; });
    dropZone.addEventListener('dragleave', () => { dropZone.style.transform = ''; });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault(); dropZone.style.transform = '';
        handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', (e) => { handleFiles(e.target.files); });

    function handleFiles(files) {
        let added = 0;
        for (let i = 0; i < files.length; i++) {
            if (selectedFiles.length >= 5) {
                alert('🚨 사진은 최대 5장까지만 분석합니다!');
                break;
            }
            if (!files[i].type.startsWith('image/')) continue;
            
            processAndCompressImage(files[i]);
            added++;
        }
        if(added > 0) {
            tickSound.currentTime = 0; tickSound.play().catch(console.warn);
        }
    }

    function processAndCompressImage(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                // Resize if needed to save API payload size
                const canvas = document.createElement('canvas');
                const MAX_WIDTH = 1000;
                const MAX_HEIGHT = 1600;
                let width = img.width;
                let height = img.height;

                if (width > height) {
                  if (width > MAX_WIDTH) { height *= MAX_WIDTH / width; width = MAX_WIDTH; }
                } else {
                  if (height > MAX_HEIGHT) { width *= MAX_HEIGHT / height; height = MAX_HEIGHT; }
                }

                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                canvas.toBlob((blob) => {
                    const compressedFile = new File([blob], file.name, { type: 'image/jpeg', lastModified: Date.now() });
                    const compressedUrl = canvas.toDataURL('image/jpeg', 0.85); // 85% quality
                    
                    selectedFiles.push({ file: compressedFile, dataUrl: compressedUrl });
                    renderThumbnails();
                }, 'image/jpeg', 0.85);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    function renderThumbnails() {
        if (selectedFiles.length === 0) {
            uploadContentUi.classList.remove('hidden');
            thumbnailListUi.classList.add('hidden');
            thumbnailListUi.innerHTML = '';
            document.getElementById('scanner-preview').src = '';
            return;
        }

        uploadContentUi.classList.add('hidden');
        thumbnailListUi.classList.remove('hidden');
        thumbnailListUi.innerHTML = '';

        selectedFiles.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'thumbnail-item';
            div.innerHTML = `<img src="${item.dataUrl}"><button class="remove-thumb-btn" data-index="${index}">X</button>`;
            thumbnailListUi.appendChild(div);
        });

        // Event delegation for remove buttons
        const rmBtns = thumbnailListUi.querySelectorAll('.remove-thumb-btn');
        rmBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation(); // prevent opening file dialog
                const idx = e.target.getAttribute('data-index');
                selectedFiles.splice(idx, 1);
                renderThumbnails();
            });
        });
        
        // Update scanner preview with the first image
        document.getElementById('scanner-preview').src = selectedFiles[0].dataUrl;
    }

    // Phase 1 -> Phase 2: Analyze Trigger
    analyzeBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) {
            alert('🚨 카톡 스샷부터 올려!');
            analyzeBtn.style.animation = 'vibrate 0.1s linear infinite';
            setTimeout(() => { analyzeBtn.style.animation = ''; }, 300);
            return;
        }

        // Show Scanner Phase
        mainUi.classList.add('hidden');
        scannerUi.classList.remove('hidden');
        document.body.style.animation = 'glitch 0.2s infinite';
        
        // Cycle buildup texts dynamically based on multiple images
        const txtEl = document.getElementById('loading-text');
        const numImages = selectedFiles.length;
        let scanSequence = [];
        
        for (let i = 1; i <= numImages; i++) {
            scanSequence.push(`${i}번 스샷 스캔 중...`);
            scanSequence.push(`${i}번 스샷 감정의 골 파악 중...`);
        }
        scanSequence.push("심층 관계 흐름(기승전결) 병합 중...");
        scanSequence.push("최종 심리 상태 렌더링 중...");

        let tidx = 0;
        txtEl.innerText = scanSequence[tidx];
        statusInterval = setInterval(() => {
            tidx = (tidx + 1) % scanSequence.length;
            txtEl.innerText = scanSequence[tidx];
        }, 800);

        try {
            // Call FastAPI 
            const formData = new FormData();
            selectedFiles.forEach(f => {
                formData.append("files", f.file);
            });
            const res = await fetch("http://localhost:8000/analyze", { method: "POST", body: formData });
            analysisResult = await res.json();
            
            // Check for format error fallback
            if(!analysisResult.fact_bombs) throw new Error("Format error");
        } catch (err) {
            console.error(err);
            analysisResult = { 
                temperature: -99, 
                power_struggle_index: 100, 
                d_day: "어제 끝남", 
                insight_report: ["님이 올린 캡처 여러 장을 보니 서버도 빡쳐서 터짐.", "둘 다 대화에 영혼이 없음. 흐름이고 뭐고 가망 없음."],
                fact_bombs: ["서버 에러 터져서 팩폭 불가.", "근데 넌 그래도 호구야.","명심해라."]
            };
        }

        // Delay extended to +2s per user request to build tension
        setTimeout(() => {
            clearInterval(statusInterval);
            document.body.style.animation = '';
            scannerUi.classList.add('hidden');
            mockAdModal.classList.remove('hidden');
        }, 1500 + (numImages * 500)); // Dynamic delay makes them feel it's working harder
    });

    // Close Ad -> Explosion -> Result
    closeAdBtn.addEventListener('click', () => {
        mockAdModal.classList.add('hidden');
        boomSound.currentTime = 0; boomSound.play().catch(console.warn);
        
        // Bind data
        document.getElementById('res-temp').innerText = analysisResult.temperature + "°C";
        document.getElementById('res-power').innerText = analysisResult.power_struggle_index + "%";
        document.getElementById('res-dday').innerText = analysisResult.d_day;
        
        // Bind insights
        const insightBox = document.getElementById('res-insight');
        if (insightBox && analysisResult.insight_report) {
            insightBox.innerHTML = '';
            analysisResult.insight_report.forEach(insight => {
                const p = document.createElement('p');
                p.textContent = insight;
                insightBox.appendChild(p);
            });
        }

        const factsBox = document.getElementById('res-facts');
        factsBox.innerHTML = '';
        analysisResult.fact_bombs.forEach(bomb => {
            const div = document.createElement('div');
            div.className = 'fact-bomb';
            div.textContent = bomb;
            factsBox.appendChild(div);
        });

        // Add extreme shock visually
        document.body.style.backgroundColor = "white";
        setTimeout(() => {
            document.body.style.backgroundColor = "";
            resultUi.classList.remove('hidden');
        }, 150);
    });

    // Retry
    retryBtn.addEventListener('click', () => {
        resultUi.classList.add('hidden');
        mainUi.classList.remove('hidden');
        selectedFiles = [];
        renderThumbnails();
    });

    // Capture & Download (html2canvas)
    captureBtn.addEventListener('click', async () => {
        const captureArea = document.getElementById('capture-area');
        captureBtn.innerHTML = "📸 박제 중...";
        
        try {
            const canvas = await html2canvas(captureArea, {
                scale: 2, // higher res
                backgroundColor: "#000000",
                useCORS: true
            });
            const link = document.createElement('a');
            link.download = `relationship_death_sentence_${Date.now()}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
            captureBtn.innerHTML = "✔️ 박제 완료";
        } catch(e) {
            console.error("Capture err", e);
            alert("박제 실패ㅠㅠ 폰 캡처 기능을 쓰십시오!");
        }
        
        setTimeout(() => { 
            captureBtn.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg> 이 굴욕 박제하기`; 
        }, 2000);
    });
});
