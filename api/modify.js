export const config = {
  api: {
    bodyParser: true,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { instruction, targetFile, apiKey, baseUrl, model } = req.body;

  if (!instruction) {
    return res.status(400).json({ error: 'Missing instruction' });
  }

  // API configuration - support both env vars and request-time override
  const apiConfig = {
    key: apiKey || process.env.OPENAI_API_KEY || 'not-set',
    url: baseUrl || process.env.OPENAI_BASE_URL || 'https://open.palebluedot.ai/v1',
    modelName: model || process.env.AI_MODEL || 'anthropic/claude-opus-4.6'
  };

  if (apiConfig.key === 'not-set') {
    return res.status(400).json({ 
      error: 'API key not configured',
      hint: 'Pass apiKey in request body or set OPENAI_API_KEY environment variable'
    });
  }

  // Current file contents (in production, fetch from Git/blob)
  const fileContents = {
    'public/index.html': `<!-- Upload page - STL file drag & drop, max 5MB -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>STL Online Preview</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      background: linear-gradient(135deg, #1a1a2e, #16213e);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }
    .upload-area {
      border: 2px dashed rgba(255,255,255,0.3);
      border-radius: 20px;
      padding: 60px 40px;
      text-align: center;
      cursor: pointer;
      max-width: 500px;
    }
  </style>
</head>
<body>
  <h1>3D STL Preview</h1>
  <div class="upload-area">Drag STL file here</div>
</body>
</html>`,
    'api/upload.js': `// Upload handler - stores STL to Vercel Blob, generates 3D preview HTML`,
    'public/modify.html': `<!-- Natural language modification interface -->`
  };

  const currentContent = fileContents[targetFile] || fileContents['public/index.html'];

  // Build the prompt
  const systemPrompt = `You are an expert web developer. You will receive:
1. A target file path
2. A natural language instruction for what change to make
3. The current file content

Your task:
- Understand the instruction
- Generate the complete modified file content
- Return ONLY the complete modified file content
- No markdown fences, no explanations, just pure code/content`;

  const userPrompt = `Target file: ${targetFile}

Current content:
${currentContent}

Instruction: ${instruction}

Generate the modified file content (pure content only, no markdown):`;

  try {
    // OpenAI-compatible API call
    const response = await fetch(`${apiConfig.url}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiConfig.key}`,
      },
      body: JSON.stringify({
        model: apiConfig.modelName,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.3,
        max_tokens: 4096,
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('AI API error:', response.status, errorText);
      return res.status(response.status).json({ 
        error: 'AI API request failed',
        details: errorText,
        hint: 'Check your API key and base URL'
      });
    }

    const data = await response.json();
    const modifiedContent = data.choices?.[0]?.message?.content?.trim() || currentContent;

    return res.status(200).json({
      success: true,
      message: 'Code modification generated',
      data: {
        instruction,
        targetFile,
        modifiedContent,
        diff: {
          file: targetFile,
          originalLength: currentContent.length,
          newLength: modifiedContent.length,
        },
        api: {
          baseUrl: apiConfig.url,
          model: apiConfig.modelName
        }
      }
    });

  } catch (error) {
    console.error('Modify error:', error);
    return res.status(500).json({ 
      error: 'Modification failed',
      message: error.message
    });
  }
}