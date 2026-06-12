import io
from typing import Optional
from PIL import Image, ImageEnhance
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn

app = FastAPI(title="Annapurna Pdf Maker")

HTML_PART_1 = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Annapurna Pdf Maker</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { background: #0f172a; color: #f3f4f6; font-family: 'Inter', sans-serif; -webkit-tap-highlight-color: transparent; min-height: 100vh; }
        .glass-panel { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); border-radius: 20px; }
        .upload-box { border: 1.5px dashed rgba(255, 255, 255, 0.2); border-radius: 16px; transition: all 0.3s ease; background: rgba(0, 0, 0, 0.2); }
        .upload-box:active { background: rgba(255, 255, 255, 0.05); border-color: #3b82f6; }
        .glass-input { background: rgba(0, 0, 0, 0.2); border: 1px solid rgba(255, 255, 255, 0.1); color: #ffffff; }
        .glass-input:focus { border-color: #3b82f6; outline: none; }
        .loader { border: 2px solid rgba(255,255,255,0.1); border-top: 2px solid #ffffff; border-radius: 50%; width: 18px; height: 18px; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #cropModal { display: none; position: fixed; inset: 0; background: #000000; z-index: 100; flex-direction: column; }
        .cropper-view-box, .cropper-face { border-radius: 8px; }
        .cropper-line, .cropper-point { background-color: #3b82f6; opacity: 0.9; }
        .cropper-point { width: 15px; height: 15px; }
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 20px; width: 20px; border-radius: 50%; background: #ffffff; cursor: pointer; margin-top: -8px; box-shadow: 0 2px 10px rgba(0,0,0,0.5); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: rgba(255,255,255,0.2); border-radius: 2px; }
        .tool-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 10px; width: 60px; height: 60px; color: #a1a1aa; transition: all 0.2s; }
        .tool-btn:active { background: rgba(255,255,255,0.1); color: #ffffff; }
        .tool-btn.active { background: rgba(59, 130, 246, 0.2); border-color: #3b82f6; color: #3b82f6; }
        .tab-btn { flex: 1; padding: 10px; text-align: center; font-size: 13px; font-weight: 600; color: #9ca3af; border-radius: 12px; transition: 0.2s; }
        .tab-btn.active { background: #3b82f6; color: #ffffff; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
    </style>
</head>
<body class="p-4 md:p-6 flex flex-col items-center pb-20">
    <div class="w-full max-w-md flex flex-col gap-5">
        <div class="glass-panel p-6 flex flex-col items-center justify-center text-center gap-2">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            <div>
                <h1 class="text-xl font-bold tracking-wide text-white">Annapurna Pdf Maker</h1>
                <p class="text-[10px] text-gray-400 font-semibold tracking-widest uppercase mt-1">Smart Merge & Crop Engine</p>
            </div>
        </div>
        <div class="glass-panel p-1.5 flex gap-1 bg-black/30">
            <button id="tabSingle" class="tab-btn" onclick="switchMode('single')">Single Side</button>
            <button id="tabDouble" class="tab-btn active" onclick="switchMode('double')">Front & Back</button>
        </div>
        <div class="grid grid-cols-2 gap-4" id="uploadContainer">
            <div class="flex flex-col gap-2 relative col-span-1" id="frontWrapper">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest pl-1" id="frontLabel">Front Side</span>
                <div class="upload-box h-48 flex flex-col items-center justify-center cursor-pointer relative overflow-hidden" onclick="triggerInput('front')">
                    <img id="frontPreview" class="hidden absolute inset-0 w-full h-full object-contain bg-black/50" />
                    <div id="frontPlaceholder" class="flex flex-col items-center text-gray-500 pointer-events-none">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="mb-3"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                        <span class="text-xs font-medium tracking-wide">Add Front</span>
                    </div>
                </div>
                <input type="file" id="frontInput" accept="image/*" class="hidden" onchange="loadFile(event, 'front')">
            </div>
            <div class="flex flex-col gap-2 relative col-span-1" id="backWrapper">
                <span class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest pl-1">Back Side</span>
                <div class="upload-box h-48 flex flex-col items-center justify-center cursor-pointer relative overflow-hidden" onclick="triggerInput('back')">
                    <img id="backPreview" class="hidden absolute inset-0 w-full h-full object-contain bg-black/50" />
                    <div id="backPlaceholder" class="flex flex-col items-center text-gray-500 pointer-events-none">
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="mb-3"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                        <span class="text-xs font-medium tracking-wide">Add Back</span>
                    </div>
                </div>
                <input type="file" id="backInput" accept="image/*" class="hidden" onchange="loadFile(event, 'back')">
            </div>
        </div>
        <div id="swapControls" class="glass-panel p-3 flex justify-between items-center bg-blue-900/20 border-blue-500/30">
            <div class="flex flex-col">
                <span class="text-xs font-semibold text-blue-400">A4 Page Layout</span>
                <span id="orderStatus" class="text-[10px] text-gray-400 mt-0.5">Front on Top | Back on Bottom</span>
            </div>
            <button onclick="toggleLayoutOrder()" class="p-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white transition-colors">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 3 21 3 21 8"></polyline><line x1="4" y1="14" x2="21" y2="3"></line><polyline points="8 21 3 21 3 16"></polyline><line x1="20" y1="10" x2="3" y2="21"></line></svg>
            </button>
        </div>
        <div class="glass-panel p-6 flex flex-col gap-6">
            <div class="flex flex-col gap-2">
                <label class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest pl-1">Custom File Name</label>
                <div class="relative">
                    <input type="text" id="fileName" placeholder="Annapurna_Document" class="glass-input w-full text-sm rounded-xl block p-3.5 pr-12">
                    <span class="absolute right-4 top-4 text-xs font-semibold text-gray-500">.pdf</span>
                </div>
            </div>
            <div class="flex flex-col gap-2">
                <label class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest pl-1">Filter Mode</label>
                <select id="scanMode" class="glass-input w-full text-sm rounded-xl block p-3.5 appearance-none">
                    <option value="annapurna" class="bg-gray-900 text-white">Scanner B&W (Govt Optimize)</option>
                    <option value="hd" class="bg-gray-900 text-white">Color HD (Natural Enhance)</option>
                    <option value="original" class="bg-gray-900 text-white">Original Photo</option>
                </select>
            </div>
            <div class="flex flex-col gap-3">
                <div class="flex justify-between items-center pl-1">
                    <label class="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">A4 Scale Adjust</label>
                    <span id="scaleValue" class="text-xs font-semibold text-white">90%</span>
                </div>
                <input type="range" id="imageScale" min="50" max="100" value="90" oninput="document.getElementById('scaleValue').textContent = this.value + '%'">
            </div>
            <button onclick="submitDocuments()" id="processBtn" class="w-full bg-white text-black py-4 rounded-xl font-bold tracking-wide flex items-center justify-center gap-2 mt-2 transition-transform active:scale-[0.98]">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" id="btnIcon"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                <span id="btnText">Download PDF (< 200KB)</span>
                <div id="loadingSpinner" class="loader hidden"></div>
            </button>
        </div>
    </div>
    <div id="cropModal" class="flex">
        <div class="p-4 flex justify-between items-center bg-[#0a0a0a] border-b border-gray-800 z-10">
            <button onclick="closeCropper()" class="p-2 text-gray-400 active:text-white">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
            <span class="text-sm font-semibold tracking-wider text-white">ADJUST PHOTO</span>
            <button onclick="confirmCrop()" class="px-5 py-1.5 bg-blue-600 text-white rounded-full font-semibold text-sm active:bg-blue-500">Save</button>
        </div>
        <div class="flex-1 overflow-hidden relative bg-[#0a0a0a]">
            <img id="imageToCrop" class="max-w-full max-h-full block" />
        </div>
        <div class="bg-[#111] pb-8 pt-5 px-4 flex flex-col gap-6 rounded-t-3xl border-t border-gray-800 z-10">
            <div class="flex flex-col gap-3 px-2">
                <div class="flex justify-between items-center text-xs text-gray-500 font-medium">
                    <span>-45°</span>
                    <span id="angleValue" class="text-white font-semibold">0°</span>
                    <span>+45°</span>
                </div>
                <input type="range" id="straightenSlider" min="-45" max="45" value="0" oninput="straightenImage(this.value)">
                <div class="text-center text-[10px] font-semibold text-gray-400 uppercase tracking-widest mt-1">Straighten</div>
            </div>
            <div class="flex justify-center gap-3">
                <button onclick="toggleFlip('X')" class="tool-btn items-center">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16 3 21 8 16 13"></polyline><line x1="21" y1="8" x2="3" y2="8"></line><polyline points="8 21 3 16 8 11"></polyline><line x1="3" y1="16" x2="21" y2="16"></line></svg>
                    <span class="text-[9px] font-medium mt-1">Flip H</span>
                </button>
                <button onclick="toggleFlip('Y')" class="tool-btn items-center">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="transform: rotate(90deg);"><polyline points="16 3 21 8 16 13"></polyline><line x1="21" y1="8" x2="3" y2="8"></line><polyline points="8 21 3 16 8 11"></polyline><line x1="3" y1="16" x2="21" y2="16"></line></svg>
                    <span class="text-[9px] font-medium mt-1">Flip V</span>
                </button>
                <button onclick="rotateCrop()" class="tool-btn items-center">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                    <span class="text-[9px] font-medium mt-1">Rotate</span>
                </button>
                <button onclick="setRatio(NaN, this)" class="tool-btn items-center active" id="btnFree">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
                    <span class="text-[9px] font-medium mt-1">Free</span>
                </button>
                <button onclick="setRatio(3/4, this)" class="tool-btn items-center" id="btnA4">
                    <svg width="18" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect></svg>
                    <span class="text-[9px] font-medium mt-1">Document</span>
                </button>
            </div>
        </div>
    </div>
"""
HTML_PART_2 = """
    <script>
        let cropper = null;
        let currentTarget = null;
        let filesData = { front: null, back: null };
        let docMode = 'double'; 
        let layoutOrder = 'front_top'; 
        let flipX = 1;
        let flipY = 1;

        function switchMode(mode) {
            docMode = mode;
            document.getElementById('tabSingle').classList.remove('active');
            document.getElementById('tabDouble').classList.remove('active');
            
            const frontWrapper = document.getElementById('frontWrapper');
            const backWrapper = document.getElementById('backWrapper');
            const frontLabel = document.getElementById('frontLabel');
            const frontBox = frontWrapper.querySelector('.upload-box');
            const swapControls = document.getElementById('swapControls');

            if (mode === 'single') {
                document.getElementById('tabSingle').classList.add('active');
                frontWrapper.classList.replace('col-span-1', 'col-span-2');
                frontBox.classList.replace('h-48', 'h-56');
                backWrapper.classList.add('hidden');
                swapControls.classList.add('hidden');
                frontLabel.textContent = "DOCUMENT PHOTO";
                filesData.back = null; 
            } else {
                document.getElementById('tabDouble').classList.add('active');
                frontWrapper.classList.replace('col-span-2', 'col-span-1');
                frontBox.classList.replace('h-56', 'h-48');
                backWrapper.classList.remove('hidden');
                swapControls.classList.remove('hidden');
                frontLabel.textContent = "FRONT SIDE";
            }
        }

        function toggleLayoutOrder() {
            if(layoutOrder === 'front_top') {
                layoutOrder = 'back_top';
                document.getElementById('orderStatus').textContent = "Back on Top | Front on Bottom";
            } else {
                layoutOrder = 'front_top';
                document.getElementById('orderStatus').textContent = "Front on Top | Back on Bottom";
            }
        }

        function triggerInput(target) {
            document.getElementById(target + 'Input').click();
        }

        function loadFile(event, target) {
            const file = event.target.files[0];
            if (!file) return;

            currentTarget = target;
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('imageToCrop').src = e.target.result;
                document.getElementById('cropModal').style.display = 'flex';
                
                flipX = 1; flipY = 1;
                document.getElementById('straightenSlider').value = 0;
                document.getElementById('angleValue').textContent = "0°";
                
                if (cropper) cropper.destroy();
                cropper = new Cropper(document.getElementById('imageToCrop'), {
                    viewMode: 1,
                    dragMode: 'crop',
                    autoCropArea: 0.95,
                    background: false,
                    guides: true,
                    center: true,
                    highlight: false,
                    cropBoxMovable: true,
                    cropBoxResizable: true,
                    toggleDragModeOnDblclick: false
                });
            }
            reader.readAsDataURL(file);
        }

        function closeCropper() {
            document.getElementById('cropModal').style.display = 'none';
            if (cropper) cropper.destroy();
            document.getElementById(currentTarget + 'Input').value = "";
        }

        function straightenImage(val) {
            if (cropper) {
                cropper.rotateTo(Number(val));
                document.getElementById('angleValue').textContent = val + "°";
            }
        }

        function toggleFlip(axis) {
            if (!cropper) return;
            if (axis === 'X') { flipX = flipX === 1 ? -1 : 1; cropper.scaleX(flipX); }
            if (axis === 'Y') { flipY = flipY === 1 ? -1 : 1; cropper.scaleY(flipY); }
        }

        function rotateCrop() {
            if (cropper) cropper.rotate(90);
        }

        function setRatio(ratio, btn) {
            if (cropper) cropper.setAspectRatio(ratio);
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        function confirmCrop() {
            if (!cropper) return;
            const canvas = cropper.getCroppedCanvas({
                maxWidth: 1500, maxHeight: 1500, fillColor: '#fff'
            });

            canvas.toBlob((blob) => {
                filesData[currentTarget] = blob;
                const previewImg = document.getElementById(currentTarget + 'Preview');
                previewImg.src = URL.createObjectURL(blob);
                previewImg.classList.remove('hidden');
                document.getElementById(currentTarget + 'Placeholder').classList.add('hidden');
                closeCropper();
            }, 'image/jpeg', 0.95);
        }

        async function submitDocuments() {
            if (!filesData.front) {
                return alert("Please upload the main document first.");
            }
            if (docMode === 'double' && !filesData.back) {
                return alert("Please upload the back side, or switch to 'Single Side' mode.");
            }

            const formData = new FormData();
            formData.append("front", filesData.front, "front.jpg");
            if (docMode === 'double' && filesData.back) {
                formData.append("back", filesData.back, "back.jpg");
            }
            
            let fileName = document.getElementById('fileName').value.trim();
            if (!fileName) fileName = "Annapurna_Document";
            
            formData.append("mode", document.getElementById('scanMode').value);
            formData.append("filename", fileName);
            formData.append("scale", document.getElementById('imageScale').value);
            formData.append("doc_type", docMode);
            formData.append("layout_order", layoutOrder); 

            const btnText = document.getElementById('btnText');
            const btnIcon = document.getElementById('btnIcon');
            const spinner = document.getElementById('loadingSpinner');
            
            btnText.textContent = "Processing Engine...";
            btnIcon.classList.add('hidden');
            spinner.classList.remove('hidden');

            try {
                const response = await fetch("/process/", {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    throw new Error("Server processing error");
                }

                const blob = await response.blob();
                if (blob.size === 0) {
                    throw new Error("Empty file returned");
                }

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
                }, 100);

            } catch (error) {
                alert("Processing Failed! Please ensure Python backend is running without errors.");
                console.error(error);
            } finally {
                btnText.textContent = "Download PDF (< 200KB)";
                btnIcon.classList.remove('hidden');
                spinner.classList.add('hidden');
            }
        }
    </script>
</body>
</html>
"""
# HTML Compilation
HTML_UI = HTML_PART_1 + HTML_PART_2

@app.get("/")
async def serve_frontend():
    return HTMLResponse(content=HTML_UI)

def enhance_image(img: Image.Image, mode: str) -> Image.Image:
    if mode == "original":
        return img
    if mode == "annapurna":
        img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.5)
        img = ImageEnhance.Brightness(img).enhance(1.2)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        return img.convert('RGB')
    if mode == "hd":
        img = ImageEnhance.Color(img).enhance(1.4)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        return img

@app.post("/process/")
async def process_document_backend(
    front: UploadFile = File(...),
    back: Optional[UploadFile] = File(None),
    mode: str = Form(...),
    filename: str = Form(...),
    scale: int = Form(...),
    doc_type: str = Form(...),
    layout_order: str = Form(...) 
):
    front_bytes = await front.read()
    img_front = Image.open(io.BytesIO(front_bytes)).convert('RGB')
    img_front = enhance_image(img_front, mode)

    img_back = None
    if doc_type == 'double' and back:
        back_bytes = await back.read()
        img_back = Image.open(io.BytesIO(back_bytes)).convert('RGB')
        img_back = enhance_image(img_back, mode)

    a4_width, a4_height = 794, 1123
    a4_canvas = Image.new('RGB', (a4_width, a4_height), (255, 255, 255))

    scale_factor = scale / 100.0
    padding_x = int((a4_width - (a4_width * scale_factor)) / 2)
    padding_y = int((a4_height - (a4_height * scale_factor)) / 2)

    if img_back:
        max_w = a4_width - (padding_x * 2)
        max_h = (a4_height // 2) - padding_y - 20
        
        top_img = img_front if layout_order == 'front_top' else img_back
        bottom_img = img_back if layout_order == 'front_top' else img_front

        top_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        offset_x_top = (a4_width - top_img.width) // 2
        offset_y_top = padding_y
        a4_canvas.paste(top_img, (offset_x_top, offset_y_top))
        
        bottom_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        offset_x_bottom = (a4_width - bottom_img.width) // 2
        offset_y_bottom = (a4_height // 2) + 20
        a4_canvas.paste(bottom_img, (offset_x_bottom, offset_y_bottom))
    else:
        max_w = a4_width - (padding_x * 2)
        max_h = a4_height - (padding_y * 2)
        
        img_front.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        offset_x = (a4_width - img_front.width) // 2
        offset_y = (a4_height - img_front.height) // 2
        a4_canvas.paste(img_front, (offset_x, offset_y))

    quality = 85
    jpeg_buffer = io.BytesIO()
    
    while True:
        jpeg_buffer.seek(0)
        jpeg_buffer.truncate()
        a4_canvas.save(jpeg_buffer, format="JPEG", quality=quality, optimize=True)
        size_kb = jpeg_buffer.tell() / 1024
        
        if size_kb <= 190 or quality <= 15:
            break
        quality -= 10

    jpeg_buffer.seek(0)
    
    pdf_buffer = io.BytesIO()
    img_for_pdf = Image.open(jpeg_buffer)
    img_for_pdf.save(pdf_buffer, format="PDF", resolution=96.0)
    
    pdf_buffer.seek(0)

    safe_filename = "".join(x for x in filename if x.isalnum() or x in " _-")
    if not safe_filename: 
        safe_filename = "Annapurna_Document"

    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}.pdf"'}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
