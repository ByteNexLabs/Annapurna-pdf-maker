import io
import logging
from typing import Optional
from PIL import Image, ImageEnhance, ImageOps
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Annapurna PDF Straightener Pro")

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
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; }
        #cropModal { display: none; position: fixed; inset: 0; background: #000; z-index: 999; flex-direction: column; }
    </style>
</head>
<body class="p-4 flex flex-col items-center">
    <div class="w-full max-w-lg glass p-6 mb-6 text-center">
        <h1 class="text-2xl font-black text-blue-500">ANNAPURNA PDF PRO</h1>
        <p class="text-xs font-bold uppercase">Professional Straightener & Scanner</p>
    </div>

    <div class="grid grid-cols-2 gap-4 w-full max-w-lg mb-6">
        <div onclick="trigger('front')" class="border-2 border-dashed border-gray-600 h-32 rounded-xl flex items-center justify-center cursor-pointer">Front</div>
        <div onclick="trigger('back')" class="border-2 border-dashed border-gray-600 h-32 rounded-xl flex items-center justify-center cursor-pointer">Back</div>
        <input type="file" id="frontInput" class="hidden" onchange="load(event, 'front')">
        <input type="file" id="backInput" class="hidden" onchange="load(event, 'back')">
    </div>

    <div class="w-full max-w-lg glass p-6 flex flex-col gap-4">
        <input type="text" id="fileName" placeholder="File Name" class="w-full p-4 bg-white/5 rounded-xl border border-white/10">
        <select id="mode" class="w-full p-4 bg-white/5 rounded-xl border border-white/10">
            <option value="bw">Scanner B&W (Govt Clean)</option>
            <option value="hd">Natural Color HD</option>
        </select>
        <button onclick="submit()" id="btn" class="w-full bg-blue-600 py-4 rounded-xl font-bold text-lg">Generate PDF</button>
    </div>

    <div id="cropModal">
        <div class="p-4 flex justify-between bg-black">
            <button onclick="closeModal()">Cancel</button>
            <span class="text-sm">Magnifier Active</span>
            <button onclick="saveCrop()" class="text-blue-500 font-bold">Apply</button>
        </div>
        <div class="flex-1 flex items-center justify-center overflow-auto">
            <img id="imageToCrop" style="max-width:100%">
        </div>
        <div class="p-4 bg-black flex gap-2">
            <button onclick="cropper.rotate(-90)" class="p-2 bg-gray-800 rounded">Rotate</button>
            <button onclick="cropper.setDragMode('move')" class="p-2 bg-gray-800 rounded">Move</button>
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
                cropper = new Cropper(document.getElementById('imageToCrop'), {
                    viewMode: 1,
                    zoomable: true,
                    ready: function() { this.cropper.setDragMode('crop'); }
                });
            };
            reader.readAsDataURL(e.target.files[0]);
        }
        function closeModal() { document.getElementById('cropModal').style.display = 'none'; cropper.destroy(); }
        function saveCrop() {
            cropper.getCroppedCanvas({width: 1500}).toBlob(b => {
                files[current] = b;
                closeModal();
            }, 'image/jpeg', 0.9);
        }
        async function submit() {
            const fd = new FormData();
            fd.append("front", files.front);
            fd.append("back", files.back || new Blob());
            fd.append("mode", document.getElementById('mode').value);
            fd.append("filename", document.getElementById('fileName').value || "Annapurna_Doc");
            document.getElementById('btn').innerText = "Processing...";
            const res = await fetch("/process/", {method:"POST", body:fd});
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a'); a.href = url; a.download = "Doc.pdf"; a.click();
            document.getElementById('btn').innerText = "Generate PDF";
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def get_index(): return HTMLResponse(content=HTML_UI)

@app.post("/process/")
async def process_doc(front: UploadFile = File(...), back: Optional[UploadFile] = File(None), mode: str = Form(...), filename: str = Form(...)):
    f_data = await front.read()
    img = Image.open(io.BytesIO(f_data)).convert('RGB')
    
    if mode == "bw":
        img = ImageEnhance.Contrast(img.convert('L')).enhance(2.5).convert('RGB')
    
    pdf_io = io.BytesIO()
    img.save(pdf_io, format="PDF", resolution=96.0, quality=80)
    pdf_io.seek(0)
    return StreamingResponse(pdf_io, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
