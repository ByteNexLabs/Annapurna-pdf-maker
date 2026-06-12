import io
import logging
from typing import Optional
from PIL import Image, ImageEnhance
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn

# 1. Logging Configuration for Render Debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. FastAPI Application Initialization
app = FastAPI(title="Annapurna PDF Professional Suite")

# 3. HTML Frontend Module (Professional Interface)
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Annapurna PDF Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.5.13/cropper.min.js"></script>
    <style>
        body { background: #020617; color: #f8fafc; font-family: sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; }
        .upload-box { border: 2px dashed #475569; border-radius: 16px; height: 180px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.3s; }
        .upload-box:hover { border-color: #3b82f6; }
        #cropModal { display: none; position: fixed; inset: 0; background: #000; z-index: 999; flex-direction: column; }
    </style>
</head>
<body class="p-4 flex flex-col items-center">
    <div class="w-full max-w-lg glass p-6 mb-6 text-center">
        <h1 class="text-3xl font-black text-blue-500">ANNAPURNA PRO</h1>
        <p class="text-xs text-gray-400 font-bold uppercase mt-1">Professional Document Processor</p>
    </div>

    <div class="grid grid-cols-2 gap-4 w-full max-w-lg mb-6">
        <div onclick="trigger('front')" class="upload-box col-span-1" id="frontBox">Front</div>
        <div onclick="trigger('back')" class="upload-box col-span-1" id="backBox">Back</div>
        <input type="file" id="frontInput" class="hidden" onchange="load(event, 'front')">
        <input type="file" id="backInput" class="hidden" onchange="load(event, 'back')">
    </div>

    <div class="w-full max-w-lg glass p-6 flex flex-col gap-4">
        <input type="text" id="fileName" placeholder="Enter File Name" class="w-full p-4 bg-white/5 rounded-xl border border-white/10">
        <select id="mode" class="w-full p-4 bg-white/5 rounded-xl border border-white/10">
            <option value="annapurna">Scanner B&W (Govt Clean)</option>
            <option value="hd">Natural Color HD</option>
        </select>
        <button onclick="submit()" id="btn" class="w-full bg-blue-600 py-4 rounded-xl font-bold text-lg hover:bg-blue-700 transition">Generate PDF</button>
    </div>

    <div id="cropModal">
        <div class="p-4 flex justify-between bg-black border-b border-gray-800">
            <button onclick="closeModal()">Cancel</button>
            <button onclick="saveCrop()" class="text-blue-500 font-bold">Apply Crop</button>
        </div>
        <div class="flex-1 overflow-hidden flex items-center justify-center">
            <img id="imageToCrop" class="max-w-full">
        </div>
    </div>

    <script>
        let cropper, current, files = {front: null, back: null};
        function trigger(t) { document.getElementById(t+'Input').click(); }
        function load(e, t) {
            current = t;
            const reader = new FileReader();
            reader.onload = (ev) => {
                document.getElementById('imageToCrop').src = ev.target.result;
                document.getElementById('cropModal').style.display = 'flex';
                cropper = new Cropper(document.getElementById('imageToCrop'), { viewMode: 1 });
            };
            reader.readAsDataURL(e.target.files[0]);
        }
        function closeModal() { document.getElementById('cropModal').style.display = 'none'; cropper.destroy(); }
        function saveCrop() {
            cropper.getCroppedCanvas({maxWidth:1500, maxHeight:1500}).toBlob(b => {
                files[current] = b;
                document.getElementById(current + 'Box').innerText = "Crop Saved";
                closeModal();
            }, 'image/jpeg', 0.9);
        }
        async function submit() {
            if(!files.front) return alert("Select Front Document!");
            const fd = new FormData();
            fd.append("front", files.front);
            fd.append("back", files.back || new Blob());
            fd.append("mode", document.getElementById('mode').value);
            fd.append("filename", document.getElementById('fileName').value || "Annapurna_Scan");
            document.getElementById('btn').innerText = "Processing...";
            try {
                const res = await fetch("/process/", {method:"POST", body:fd});
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = "Document.pdf"; a.click();
            } catch(e) { alert("Server Error!"); }
            document.getElementById('btn').innerText = "Generate PDF";
        }
    </script>
</body>
</html>
"""

# 4. Backend Processing Engine
@app.get("/")
async def get_index():
    return HTMLResponse(content=HTML_UI)

@app.post("/process/")
async def process_document(
    front: UploadFile = File(...),
    back: Optional[UploadFile] = File(None),
    mode: str = Form(...),
    filename: str = Form(...)
):
    try:
        f_data = await front.read()
        front_img = Image.open(io.BytesIO(f_data)).convert('RGB')
        
        # Apply Enhancement
        if mode == "annapurna":
            front_img = ImageEnhance.Contrast(front_img.convert('L')).enhance(2.0).convert('RGB')
        
        canvas = Image.new('RGB', (794, 1123), 'white')
        canvas.paste(front_img.resize((700, 500)), (47, 50))
        
        if back:
            b_data = await back.read()
            back_img = Image.open(io.BytesIO(b_data)).convert('RGB')
            if mode == "annapurna":
                back_img = ImageEnhance.Contrast(back_img.convert('L')).enhance(2.0).convert('RGB')
            canvas.paste(back_img.resize((700, 500)), (47, 600))
            
        pdf_io = io.BytesIO()
        canvas.save(pdf_io, format="PDF", resolution=96.0, quality=85)
        pdf_io.seek(0)
        return StreamingResponse(pdf_io, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})
    except Exception as e:
        logger.error(f"Processing Error: {e}")
        raise HTTPException(status_code=500, detail="Backend Processing Failed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
