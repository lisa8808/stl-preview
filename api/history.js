import { list } from '@vercel/blob';

export const config = {
  api: {
    bodyParser: true,
  },
};

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Return mock version history
  // In full implementation, this would read from Vercel Blob or Git commits
  
  const versionHistory = {
    current: {
      version: '1.0.0',
      tag: 'v1.0.0',
      date: new Date().toISOString(),
      description: 'Initial release with STL upload and 3D preview',
      files: ['public/index.html', 'api/upload.js', 'vercel.json', 'README.md']
    },
    changelog: [
      {
        version: '1.0.0',
        date: new Date().toISOString(),
        changes: [
          'Initial release',
          'STL file upload support',
          '3D preview with Google Model Viewer',
          'AR support for mobile'
        ]
      }
    ],
    totalVersions: 1
  };

  return res.status(200).json({
    success: true,
    data: versionHistory
  });
}