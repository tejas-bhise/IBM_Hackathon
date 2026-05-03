'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { uploadProject } from '@/lib/api';
import { useProjectStore } from '@/lib/store';
import { Upload, Github, AlertCircle, Loader } from 'lucide-react';

export default function UploadPage() {
  const router = useRouter();
  const { setProjectId } = useProjectStore();
  const [githubUrl, setGithubUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
    setGithubUrl(''); // Clear URL if file selected
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!githubUrl && !file) {
      setError('Please provide either a GitHub URL or upload a file');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await uploadProject(githubUrl || undefined, file || undefined);
      console.log('Upload successful:', result);
      
      // Store project_id globally using Zustand store
      setProjectId(result.project_id);
      
      // Redirect to loading page with project_id in URL
      router.push(`/loading?project_id=${result.project_id}`);
    } catch (err) {
      console.error('Upload error:', err);
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to upload project. Please ensure the backend is running on http://127.0.0.1:8000'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-cyan-600/20 rounded-full mb-4">
            <Upload className="w-8 h-8 text-cyan-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">AI Project Intelligence</h1>
          <p className="text-slate-400">Upload your project for intelligent analysis</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-950 border border-red-700 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-300 text-sm">{error}</p>
          </div>
        )}

        {/* Upload Form */}
        <form onSubmit={handleUpload} className="space-y-6">
          {/* GitHub URL Input */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition">
            <label className="flex items-center gap-2 mb-3">
              <Github className="w-5 h-5 text-slate-400" />
              <span className="font-semibold text-white">GitHub Repository URL</span>
            </label>
            <input
              type="url"
              placeholder="https://github.com/username/repo"
              value={githubUrl}
              onChange={(e) => {
                setGithubUrl(e.target.value);
                setFile(null);
              }}
              disabled={loading || file !== null}
              className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-3 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
            />
            <p className="text-xs text-slate-400 mt-2">
              Paste the GitHub repository URL to analyze
            </p>
          </div>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-700"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-slate-900 text-slate-400">OR</span>
            </div>
          </div>

          {/* File Upload */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-slate-500 transition">
            <label className="cursor-pointer block">
              <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <span className="font-semibold text-white block mb-1">
                {file?.name || 'Upload ZIP file'}
              </span>
              <span className="text-xs text-slate-400">
                or drag and drop (.zip files)
              </span>
              <input
                type="file"
                accept=".zip"
                onChange={handleFileChange}
                disabled={loading || githubUrl !== ''}
                className="hidden"
              />
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || (!githubUrl && !file)}
            className="w-full bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2 transition"
          >
            {loading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                Analyze Project
              </>
            )}
          </button>
        </form>

        {/* Info Box */}
        <div className="mt-8 bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <p className="text-sm text-slate-300">
            <span className="font-semibold">💡 Tip:</span> You can upload a GitHub repository URL or a ZIP file containing your project code. The AI will analyze it for security issues and provide insights.
          </p>
        </div>
      </div>
    </div>
  );
}
