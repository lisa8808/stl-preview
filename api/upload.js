import { put } from '@vercel/blob';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { spawn } from 'child_process';

export const config = {
  api: {
    bodyParser: false,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // 获取上传的文件数据
    const chunks = [];
    for await (const chunk of req.body) {
      chunks.push(chunk);
    }
    const buffer = Buffer.concat(chunks);

    // 生成唯一文件名
    const timestamp = Date.now();
    const randomStr = Math.random().toString(36).substring(2, 8);
    const safeName = `stl-${timestamp}-${randomStr}`;
    const filename = `${safeName}.stl`;
    const previewFilename = `${safeName}-preview.html`;

    // 1. 上传 STL 到 Vercel Blob
    const blob = await put(filename, buffer, {
      contentType: 'application/sla',
      access: 'public',
    });

    const stlUrl = blob.url;

    // 2. 生成 3D 预览 HTML
    const previewHtml = generatePreviewHtml(safeName, stlUrl);

    // 3. 保存预览 HTML 到 Blob
    const previewBlob = await put(previewFilename, previewHtml, {
      contentType: 'text/html',
      access: 'public',
    });

    const previewUrl = previewBlob.url;

    // 4. 返回链接
    return res.status(200).json({
      success: true,
      stlUrl,
      previewUrl,
      shareUrl: `https://stl-view.vercel.app/preview/${safeName}`,
      filename: safeName,
    });

  } catch (error) {
    console.error('Upload error:', error);
    return res.status(500).json({ 
      error: 'Upload failed', 
      message: error.message 
    });
  }
}

function generatePreviewHtml(id, stlUrl) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>STL Preview - ${id}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #1a1a2e;
      color: #fff;
      height: 100vh;
      overflow: hidden;
    }
    #viewer-container {
      width: 100vw;
      height: 100vh;
    }
    model-viewer {
      width: 100%;
      height: 100%;
      --poster-color: transparent;
    }
    #controls {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
      padding: 12px 24px;
      border-radius: 50px;
      display: flex;
      gap: 16px;
      z-index: 100;
    }
    #controls a {
      color: #fff;
      text-decoration: none;
      font-size: 14px;
      padding: 8px 16px;
      border-radius: 20px;
      background: rgba(255,255,255,0.1);
      transition: background 0.2s;
    }
    #controls a:hover {
      background: rgba(255,255,255,0.2);
    }
    #loading {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 18px;
      color: rgba(255,255,255,0.7);
    }
  </style>
  <!-- Load Google Model Viewer -->
  <script type="module" src="https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js"></script>
  <script type="module">
    document.addEventListener('DOMContentLoaded', () => {
      const viewer = document.querySelector('model-viewer');
      viewer.addEventListener('load', () => {
        document.getElementById('loading').style.display = 'none';
      });
    });
  </script>
</head>
<body>
  <div id="loading">Loading 3D Model...</div>
  <div id="viewer-container">
    <model-viewer
      src="${stlUrl}"
      shadow-intensity="1"
      camera-controls
      auto-rotate
      ar
      ar-modes="webxr scene-viewer quick-look"
      alt="STL 3D Preview"
    >
    </model-viewer>
  </div>
  <div id="controls">
    <a href="${stlUrl}" download>Download STL</a>
    <a href="javascript:shareModel()">Share</a>
  </div>
  <script>
    function shareModel() {
      const url = window.location.href;
      if (navigator.share) {
        navigator.share({ title: 'STL Preview', url });
      } else {
        navigator.clipboard.writeText(url);
        alert('Link copied to clipboard!');
      }
    }
  </script>
</body>
</html>`;
}