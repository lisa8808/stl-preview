# STL Online Preview Service

A free, serverless 3D STL file preview service with AI-powered natural language modifications.

## Features

| Feature | Description |
|---------|-------------|
| 📤 **Upload** | Drag & drop STL files, max 5MB |
| 🔗 **3D Preview** | Interactive 3D viewer with Google Model Viewer |
| 📱 **AR Support** | AR Quick Look (iOS) / Scene Viewer (Android) |
| 🛠️ **AI Modify** | Natural language code modification |
| 📜 **Version History** | Full git-like version control |
| 🔄 **Rollback** | Revert to any previous version |

## Architecture

```
User uploads STL → Vercel Blob → Generate Preview HTML → Deploy → Return link
     ↓
User describes change → AI understands → Generates code diff → Apply + Version tag
```

## Tech Stack

- **Frontend**: Vanilla HTML/JS (no framework)
- **Backend**: Vercel Serverless Functions
- **Storage**: Vercel Blob (5GB free)
- **3D Viewer**: Google Model Viewer
- **AI Modify**: OpenAI API (optional, for natural language changes)

## Quick Start

### 1. Install & Login
```bash
npm i -g vercel
vercel login
```

### 2. Deploy
```bash
cd stl-preview
vercel
```

### 3. Production
```bash
vercel --prod
```

## Project Structure

```
stl-preview/
├── vercel.json           # Vercel config
├── README.md             # This file
├── api/
│   ├── upload.js         # STL upload + 3D preview generator
│   ├── modify.js         # 🌟 Natural language modification API
│   └── history.js        # 🌟 Version history API
└── public/
    ├── index.html        # Upload page
    ├── modify.html       # 🌟 AI modification interface
    └── history.html      # 🌟 Version history browser
```

## API Reference

### POST /api/upload
Upload STL file, returns preview URLs.

### POST /api/modify
Natural language code modification.
```json
{
  "instruction": "Change background to dark blue",
  "targetFile": "public/index.html"
}
```

### GET /api/history
Returns version history.

## Pages

| Page | URL | Purpose |
|------|-----|---------|
| Upload | `/` | Upload STL, get 3D preview link |
| Modify | `/modify.html` | Describe changes in natural language |
| History | `/history.html` | Browse and rollback versions |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Optional | For AI-powered natural language modifications |

## Limitations

- **File size**: 5MB max per STL file
- **Storage**: 5GB Vercel Blob free tier
- **AI Modify**: Requires OpenAI API key (pay-per-use, ~$0.01 per modification)

## License

MIT