import io
import logging
from typing import Optional
from PIL import Image, ImageEnhance, ImageFilter
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn

# ---------------------------------------------------------
# BACKEND CONFIGURATION & LOGGING
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Annapurna PDF Maker & Straightener Pro")

# ---------------------------------------------------------
# FRONTEND UI (Massive Feature-Packed HTML/JS/CSS)
# ---------------------------------------------------------
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Annapurna PDF Pro | Premium Scanner</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { 
            background-color: #020617; /* Deep SaaS Dark */
            color: #f8fafc; 
            font-family: 'Inter', sans-serif; 
            -webkit-tap-highlight-color: transparent;
            padding-bottom: 100px;
        }
        .glass-panel { 
            background: rgba(255, 255, 255, 0.03); 
            backdrop-filter: blur(16px); 
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.05); 
            border-radius: 24px; 
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        .upload-slot {
            border: 2px dashed rgba(255,255,255,0.15);
            background: rgba(0,0,0,0.4);
            border-radius: 16px;
            height: 180px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .upload-slot:active { background: rgba(59, 130, 246, 0.1); border-color: #3b82f6; }
        .slot-img-preview { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain; background: #000; z-index: 5; display: none; }
        
        .premium-input {
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            color: #fff;
            transition: border 0.3s ease;
        }
        .premium-input:focus { border-color: #3b82f6; outline: none; }
        
        /* Range Slider Styling */
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 24px; width: 24px; border-radius: 50%; background: #ffffff; cursor: pointer; margin-top: -10px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; }

        /* Cropper Customization */
        #cropModal { display: none; position: fixed; inset: 0; background: #000; z-index: 9999; flex-direction: column; }
        .cropper-view-box, .cropper-face { border-radius: 8px; }
        .cropper-point { width: 20px; height: 20px; background-color: #3b82f6; opacity: 1; }
        .cropper-line { background-color: #3b82f6; }
        
        .btn-tool { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 12px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; }
        .btn-tool:active { background: rgba(255,255,255,0.1); color: #fff; }
        
        /* Segmented Toggle */
        .toggle-container { display: flex; background: rgba(0,0,0,0.5); border-radius: 12px; padding: 4px; }
        .toggle-btn { flex: 1; padding: 12px; text-align: center; font-size: 12px; font-weight: 600; color: #64748b; border-radius: 8px; transition: 0.3s; }
        .toggle-btn.active { background: #3b82f6; color: #fff; }

        /* Accordion */
        .accordion-content { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
        .accordion-content.open { max-height: 200px; }
    </style>
</head>
<body class="flex flex-col items-center">

    <div class="w-full max-w-md mt-6 mb-6 text-center">
        <h1 class="text-3xl font-bold tracking-tight text-white">ANNAPURNA <span class="text-blue-500">PRO</span></h1>
        <p class="text-[10px] text-gray-400 font-semibold tracking-widest uppercase mt-2">Professional Document Processor</p>
    </div>

    <div class="w-full max-w-md flex flex-col gap-6 px-4">
        
        <div class="grid grid-cols-2 gap-4" id="documentGrid">
            <div class="col-span-1 flex flex-col gap-2 relative">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest pl-1" id="labelFront">Front Document</span>
                <div class="upload-slot" onclick="triggerInput('front')">
                    <img id="frontPreview" class="slot-img-preview" />
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="1.5" class="mb-3"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                    <span class="text-xs font-medium text-gray-400">Add Front</span>
                </div>
                <input type="file" id="frontInput" accept="image/*" class="hidden" onchange="loadFile(event, 'front')">
            </div>

            <div class="col-span-1 flex flex-col gap-2 relative" id="backWrapper">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest pl-1">Back Document</span>
                <div class="upload-slot" onclick="triggerInput('back')">
                    <img id="backPreview" class="slot-img-preview" />
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="1.5" class="mb-3"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                    <span class="text-xs font-medium text-gray-400">Add Back</span>
                </div>
                <input type="file" id="backInput" accept="image/*" class="hidden" onchange="loadFile(event, 'back')">
            </div>
        </div>

        <div class="glass-panel p-6 flex flex-col gap-6">
            
            <div class="flex flex-col gap-2">
                <input type="text" id="fileName" placeholder="Enter File Name (e.g. Aadhar_Card)" class="premium-input w-full text-sm rounded-xl block p-4">
            </div>

            <div class="flex flex-col gap-2">
                <select id="scanMode" class="premium-input w-full text-sm rounded-xl block p-4 appearance-none">
                    <option value="annapurna">Scanner B&W (Govt Clean - Best for Text)</option>
                    <option value="hd">Scanner Color (High Definition)</option>
                    <option value="original">Original Photo (No Filter)</option>
                </select>
            </div>

            <div class="toggle-container mt-2">
                <button id="btnSingle" class="toggle-btn" onclick="setDocMode('single')">Single Document</button>
                <button id="btnDouble" class="toggle-btn active" onclick="setDocMode('double')">Double Side (Top/Bottom)</button>
            </div>

            <div class="flex flex-col gap-4 mt-2">
                <div class="flex justify-between items-center pl-1">
                    <label class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">A4 Scale Adjust</label>
                    <span id="scaleValue" class="text-sm font-bold text-white">90%</span>
                </div>
                <input type="range" id="imageScale" min="40" max="100" value="90" oninput="updateScaleUI(this.value)">
            </div>
            
        </div>

        <button onclick="processDocuments()" id="generateBtn" class="w-full bg-blue-600 hover:bg-blue-500 text-white py-5 rounded-2xl font-bold tracking-wide flex items-center justify-center gap-3 transition-all active:scale-95 shadow-[0_0_20px_rgba(59,130,246,0.4)]">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" id="btnIcon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            <span id="btnText" class="text-lg">Generate PDF</span>
        </button>
    </div>

    <div id="cropModal">
        <div class="p-4 flex justify-between items-center bg-[#0a0a0a] border-b border-white/10 z-20">
            <button onclick="closeCropper()" class="p-2 text-gray-400">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
            <div class="flex flex-col items-center">
                <span class="text-sm font-bold tracking-wider text-white">ADJUST & STRAIGHTEN</span>
                <span class="text-[9px] text-blue-400 uppercase tracking-widest">Pinch to Zoom / Drag Corners</span>
            </div>
            <button onclick="applyCrop()" class="px-5 py-2 bg-blue-600 text-white rounded-full font-bold text-sm">DONE</button>
        </div>
        
        <div class="flex-1 overflow-hidden relative bg-[#050505] flex items-center justify-center">
            <img id="imageToCrop" class="max-w-full max-h-full block opacity-0 transition-opacity duration-300" />
        </div>
        
        <div class="bg-[#0a0a0a] p-5 flex flex-col gap-6 border-t border-white/10 z-20 pb-8">
            
            <div class="flex flex-col gap-3 px-2">
                <div class="flex justify-between items-center text-xs text-gray-400 font-medium">
                    <span>-45°</span>
                    <span id="angleReadout" class="text-white font-bold bg-white/10 px-3 py-1 rounded-full">0°</span>
                    <span>+45°</span>
                </div>
                <input type="range" id="straightenSlider" min="-45" max="45" value="0" step="0.5" oninput="straightenImage(this.value)">
                <div class="text-center text-[10px] font-semibold text-gray-500 uppercase tracking-widest mt-1">Fine Rotation (Straighten)</div>
            </div>

            <div class="grid grid-cols-4 gap-2">
                <button onclick="cropper.rotate(-90)" class="btn-tool">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><polyline points="3 3 3 8 8 8"></polyline></svg>
                    <span>Rotate</span>
                </button>
                <button onclick="toggleDragMode()" id="btnDragMode" class="btn-tool">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" id="iconDragMode"><path d="M5 9c0-2.2 1.8-4 4-4h6c2.2 0 4 1.8 4 4v6c0 2.2-1.8 4-4 4H9c-2.2 0-4-1.8-4-4V9z"></path></svg>
                    <span id="textDragMode">Move</span>
                </button>
                <button onclick="cropper.zoom(0.1)" class="btn-tool">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
                    <span>Zoom In</span>
                </button>
                <button onclick="resetCrop()" class="btn-tool">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><polyline points="3 3 3 8 8 8"></polyline></svg>
                    <span>Reset</span>
                </button>
            </div>
        </div>
    </div>

    <script>
        // --- STATE MANAGEMENT ---
        let cropper = null;
        let currentTarget = null;
        let filesData = { front: null, back: null };
        let docMode = 'double';
        let isMoveMode = false;

        // --- UI FUNCTIONS ---
        function updateScaleUI(val) {
            document.getElementById('scaleValue').textContent = val + '%';
        }

        function setDocMode(mode) {
            docMode = mode;
            const btnSingle = document.getElementById('btnSingle');
            const btnDouble = document.getElementById('btnDouble');
            const backWrapper = document.getElementById('backWrapper');
            const labelFront = document.getElementById('labelFront');
            
            if (mode === 'single') {
                btnSingle.classList.add('active');
                btnDouble.classList.remove('active');
                backWrapper.style.display = 'none';
                document.getElementById('documentGrid').classList.replace('grid-cols-2', 'grid-cols-1');
                labelFront.textContent = "DOCUMENT PHOTO";
                filesData.back = null; // Clear backend data
            } else {
                btnDouble.classList.add('active');
                btnSingle.classList.remove('active');
                backWrapper.style.display = 'flex';
                document.getElementById('documentGrid').classList.replace('grid-cols-1', 'grid-cols-2');
                labelFront.textContent = "FRONT DOCUMENT";
            }
        }

        // --- CROPPER ENGINE ---
        function triggerInput(target) {
            document.getElementById(target + 'Input').click();
        }

        function loadFile(event, target) {
            const file = event.target.files[0];
            if (!file) return;

            currentTarget = target;
            const reader = new FileReader();
            reader.onload = function(e) {
                const imgElement = document.getElementById('imageToCrop');
                imgElement.src = e.target.result;
                document.getElementById('cropModal').style.display = 'flex';
                
                // Reset Straighten Slider
                document.getElementById('straightenSlider').value = 0;
                document.getElementById('angleReadout').textContent = '0°';
                
                if (cropper) cropper.destroy();
                
                // Initialize Advanced CropperJS
                cropper = new Cropper(imgElement, {
                    viewMode: 1, // Restrict crop box to not exceed size of canvas
                    dragMode: 'crop',
                    autoCropArea: 0.95,
                    background: false,
                    guides: true,
                    center: true,
                    highlight: true,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false,
                    zoomable: true, // Crucial for Magnification
                    wheelZoomRatio: 0.1,
                    ready: function () {
                        imgElement.classList.remove('opacity-0');
                    }
                });
                isMoveMode = false;
                updateDragBtnUI();
            }
            reader.readAsDataURL(file);
        }

        function closeCropper() {
            document.getElementById('cropModal').style.display = 'none';
            document.getElementById('imageToCrop').classList.add('opacity-0');
            if (cropper) cropper.destroy();
            document.getElementById(currentTarget + 'Input').value = "";
        }

        function straightenImage(val) {
            if (cropper) {
                cropper.rotateTo(Number(val));
                document.getElementById('angleReadout').textContent = val + "°";
            }
        }

        function toggleDragMode() {
            if (!cropper) return;
            isMoveMode = !isMoveMode;
            cropper.setDragMode(isMoveMode ? 'move' : 'crop');
            updateDragBtnUI();
        }

        function updateDragBtnUI() {
            const text = document.getElementById('textDragMode');
            text.textContent = isMoveMode ? 'Crop' : 'Move';
        }

        function resetCrop() {
            if (cropper) {
                cropper.reset();
                document.getElementById('straightenSlider').value = 0;
                document.getElementById('angleReadout').textContent = '0°';
            }
        }

        function applyCrop() {
            if (!cropper) return;
            
            // Generate High Quality Cropped Canvas
            const canvas = cropper.getCroppedCanvas({
                maxWidth: 2000,
                maxHeight: 2000,
                fillColor: '#ffffff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high'
            });

            canvas.toBlob((blob) => {
                filesData[currentTarget] = blob;
                
                // Update UI Previews
                const previewImg = document.getElementById(currentTarget + 'Preview');
                previewImg.src = URL.createObjectURL(blob);
                previewImg.style.display = 'block';
                
                closeCropper();
            }, 'image/jpeg', 0.95);
        }

        // --- API COMMUNICATION ---
        async function processDocuments() {
            if (!filesData.front) {
                return alert("Please upload and crop the main document first.");
            }
            if (docMode === 'double' && !filesData.back) {
                return alert("Please upload the back side document.");
            }

            // Prepare Payload
            const formData = new FormData();
            formData.append("front", filesData.front, "front_scanned.jpg");
            if (docMode === 'double' && filesData.back) {
                formData.append("back", filesData.back, "back_scanned.jpg");
            }
            
            let fileName = document.getElementById('fileName').value.trim();
            if (!fileName) fileName = "Annapurna_Document";
            
            formData.append("mode", document.getElementById('scanMode').value);
            formData.append("filename", fileName);
            formData.append("scale", document.getElementById('imageScale').value);
            formData.append("doc_type", docMode);

            // UI Loading State
            const btn = document.getElementById('generateBtn');
            const btnText = document.getElementById('btnText');
            const btnIcon = document.getElementById('btnIcon');
            
            const originalHTML = btn.innerHTML;
            btnText.textContent = "Processing Engine...";
            btnIcon.style.display = 'none';
            btn.classList.add('opacity-80', 'cursor-not-allowed');

            try {
                const response = await fetch("/process/", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    throw new Error("Server processing error");
                }

                // Guarantee File Download
                const blob = await response.blob();
                if (blob.size === 0) throw new Error("Empty file returned");

                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;
                a.download = `${fileName}.pdf`;
                document.body.appendChild(a);
                a.click();
                
                setTimeout(() => {
                    window.URL.revokeObjectURL(downloadUrl);
                    a.remove();
                }, 200);

            } catch (error) {
                alert("PDF Generation Failed! Check server logs.");
                console.error(error);
            } finally {
                btn.innerHTML = originalHTML;
                btn.classList.remove('opacity-80', 'cursor-not-allowed');
            }
        }
    </script>
</body>
</html>
"""

# ---------------------------------------------------------
# BACKEND PROCESSOR (Pillow Image Engine & PDF Generator)
# ---------------------------------------------------------

@app.get("/")
async def serve_ui():
    return HTMLResponse(content=HTML_UI)

def apply_smart_filter(img: Image.Image, mode: str) -> Image.Image:
    """Applies advanced processing based on the selected mode"""
    if mode == "original":
        return img
        
    if mode == "annapurna":
        # Govt Standard Scanner Filter (B&W, High Sharpness, White Background)
        img = img.convert('L')
        # Boost Contrast heavily to make background white and text black
        img = ImageEnhance.Contrast(img).enhance(2.8)
        # Boost Brightness slightly
        img = ImageEnhance.Brightness(img).enhance(1.2)
        # Apply strict sharpness
        img = ImageEnhance.Sharpness(img).enhance(3.0)
        return img.convert('RGB')
        
    if mode == "hd":
        # Color HD Filter (Vibrant, Clear)
        img = ImageEnhance.Color(img).enhance(1.4)
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        return img

@app.post("/process/")
async def process_document_backend(
    front: UploadFile = File(...),
    back: Optional[UploadFile] = File(None),
    mode: str = Form(...),
    filename: str = Form(...),
    scale: int = Form(...),
    doc_type: str = Form(...)
):
    try:
        # 1. Read and Parse Front Image
        front_bytes = await front.read()
        img_front = Image.open(io.BytesIO(front_bytes)).convert('RGB')
        img_front = apply_smart_filter(img_front, mode)

        # 2. Read and Parse Back Image (if double mode)
        img_back = None
        if doc_type == 'double' and back:
            back_bytes = await back.read()
            img_back = Image.open(io.BytesIO(back_bytes)).convert('RGB')
            img_back = apply_smart_filter(img_back, mode)

        # 3. Setup Master A4 Canvas (Standard 96 DPI: 794x1123)
        A4_WIDTH, A4_HEIGHT = 794, 1123
        a4_canvas = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), (255, 255, 255))

        # 4. Calculate Scaling and Padding
        scale_factor = scale / 100.0
        padding_x = int((A4_WIDTH - (A4_WIDTH * scale_factor)) / 2)
        padding_y = int((A4_HEIGHT - (A4_HEIGHT * scale_factor)) / 2)

        # 5. Paint Canvas
        if img_back:
            # Layout: Double Sided (Top and Bottom)
            max_w = A4_WIDTH - (padding_x * 2)
            max_h = (A4_HEIGHT // 2) - padding_y - 20
            
            # Paste Front (Top Half)
            img_front.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            offset_x_front = (A4_WIDTH - img_front.width) // 2
            offset_y_front = padding_y
            a4_canvas.paste(img_front, (offset_x_front, offset_y_front))
            
            # Paste Back (Bottom Half)
            img_back.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            offset_x_back = (A4_WIDTH - img_back.width) // 2
            offset_y_back = (A4_HEIGHT // 2) + 20
            a4_canvas.paste(img_back, (offset_x_back, offset_y_back))
        else:
            # Layout: Single Sided (Center Aligned)
            max_w = A4_WIDTH - (padding_x * 2)
            max_h = A4_HEIGHT - (padding_y * 2)
            
            img_front.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            offset_x = (A4_WIDTH - img_front.width) // 2
            offset_y = (A4_HEIGHT - img_front.height) // 2
            a4_canvas.paste(img_front, (offset_x, offset_y))

        # 6. Advanced Compression Engine (Targeting strictly < 200KB)
        quality = 85
        jpeg_buffer = io.BytesIO()
        
        while True:
            jpeg_buffer.seek(0)
            jpeg_buffer.truncate()
            # optimize=True helps in reducing file size efficiently
            a4_canvas.save(jpeg_buffer, format="JPEG", quality=quality, optimize=True)
            size_kb = jpeg_buffer.tell() / 1024
            
            # Break if size is under 190KB (leaving 10KB for PDF header metadata)
            if size_kb <= 190 or quality <= 10:
                break
            quality -= 5 # Decrease aggressively to ensure fast generation

        # 7. Package JPEG into final PDF wrapper
        jpeg_buffer.seek(0)
        pdf_buffer = io.BytesIO()
        img_for_pdf = Image.open(jpeg_buffer)
        img_for_pdf.save(pdf_buffer, format="PDF", resolution=96.0)
        pdf_buffer.seek(0)

        # Clean Filename Security
        safe_filename = "".join(x for x in filename if x.isalnum() or x in " _-")
        if not safe_filename: 
            safe_filename = "Annapurna_Document"

        # 8. Dispatch Response
        return StreamingResponse(
            pdf_buffer, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}.pdf"'}
        )
        
    except Exception as e:
        logger.error(f"Annapurna Engine Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Backend Processing Failed. See server logs.")

# ---------------------------------------------------------
# SERVER LAUNCHER
# ---------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
