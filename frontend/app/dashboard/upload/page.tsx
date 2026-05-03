'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { uploadProject } from '@/lib/api';
import { useProjectStore } from '@/lib/store';
import { UploadCloud, Github, FileCode2, ArrowRight, CheckCircle2, ShieldAlert, Cpu, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

export default function UploadPage() {
  const router = useRouter();
  const { setProjectId } = useProjectStore();
  const [url, setUrl] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeRecipe, setActiveRecipe] = useState('security-audit');
  const [autoApprove, setAutoApprove] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    if (selectedFile) {
      setUrl(''); // Clear URL if file selected
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url && !file) {
      setError('Please provide either a GitHub URL or upload a file');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      /** 
       * ✅ FIX APPLIED: 
       * Passing arguments directly as (string, File) instead of an object.
       */
      const result = await uploadProject(url || undefined, file || undefined);
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
      setIsAnalyzing(false);
    }
  };

  if (isAnalyzing) {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-panel p-10 rounded-2xl max-w-md w-full text-center flex flex-col items-center border-accent/20 border shadow-[0_24px_80px_-42px_oklch(0.55_0.19_262.95_/_0.85)]"
        >
          <div className="relative mb-8">
            <div className="absolute inset-0 bg-accent/20 rounded-full blur-xl animate-pulse" />
            <div className="w-20 h-20 bg-background border border-border rounded-2xl flex items-center justify-center relative shadow-lg">
              <Cpu className="size-10 text-accent animate-bounce" />
            </div>
          </div>
          <h2 className="text-2xl font-bold mb-2">Bob is Analyzing...</h2>
          <p className="text-muted-foreground text-sm mb-6">Running '{activeRecipe}' recipe and mapping architecture.</p>
          
          <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
            <motion.div 
              className="bg-accent h-full"
              initial={{ width: '0%' }}
              animate={{ width: '100%' }}
              transition={{ duration: 2.2, ease: "easeInOut" }}
            />
          </div>
          <div className="w-full flex justify-between mt-2 text-xs text-muted-foreground font-mono">
            <span>Scanning files...</span>
            <span>Detecting PII...</span>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8 h-full flex flex-col">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight mb-2">Connect Repository</h1>
        <p className="text-muted-foreground">Upload your codebase to initialize the AI Project Intelligence Platform.</p>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="max-w-5xl mx-auto w-full mb-6">
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <p className="text-destructive text-sm">{error}</p>
          </div>
        </div>
      )}

      <div className="max-w-5xl mx-auto w-full mt-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Area */}
          <div className="glass-panel p-8 rounded-2xl border border-border/50 bg-background/50 text-center hover:border-accent/30 transition-colors border-dashed border-2">
            <div className="mx-auto w-16 h-16 bg-secondary rounded-2xl flex items-center justify-center mb-4">
              <UploadCloud className="size-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-1">
              {file?.name || 'Drag & Drop Repository'}
            </h3>
            <p className="text-sm text-muted-foreground mb-6">Support for .zip files.</p>
            <label className="cursor-pointer">
              <span className="px-6 py-2.5 bg-secondary text-foreground hover:bg-secondary/80 rounded-xl text-sm font-medium transition-colors border border-border inline-block">
                Browse Files
              </span>
              <input
                type="file"
                accept=".zip"
                onChange={handleFileChange}
                disabled={isAnalyzing || url !== ''}
                className="hidden"
              />
            </label>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border" /></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-background px-2 text-muted-foreground">Or connect via URL</span></div>
          </div>

          {/* GitHub Input */}
          <form onSubmit={handleAnalyze} className="glass-panel p-6 rounded-2xl border border-border/50 bg-background/50">
            <label className="block text-sm font-medium mb-3">GitHub Repository URL</label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Github className="size-5 text-muted-foreground" />
                </div>
                <input
                  type="url"
                  placeholder="https://github.com/organization/repo"
                  className="w-full pl-10 pr-4 py-3 bg-background border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-transparent transition-all"
                  value={url}
                  onChange={(e) => {
                    setUrl(e.target.value);
                    if (e.target.value) {
                      setFile(null); // Clear file if URL is entered
                    }
                  }}
                  disabled={isAnalyzing || file !== null}
                />
              </div>
              <button
                type="submit"
                disabled={isAnalyzing || (!url && !file)}
                className="px-6 py-3 bg-[#635BFF] text-white hover:bg-[#635BFF]/90 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-sm"
              >
                {isAnalyzing ? (
                  <>
                    <Cpu className="size-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    Connect <ArrowRight className="size-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* The Glue Phase Settings */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-border/50 bg-secondary/20">
            <div className="flex items-center gap-2 mb-4">
              <ShieldAlert className="size-5 text-accent" />
              <h3 className="font-semibold">The Glue Phase</h3>
            </div>
            <p className="text-xs text-muted-foreground mb-6">
              Configure enterprise business process and operations settings.
            </p>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Skill Recipes</label>
                <select 
                  className="w-full p-2.5 bg-background border border-border rounded-lg text-sm"
                  value={activeRecipe}
                  onChange={(e) => setActiveRecipe(e.target.value)}
                >
                  <option value="security-audit">Comprehensive Security Audit</option>
                  <option value="compliance-check">SOC2 / GDPR Compliance Check</option>
                  <option value="code-quality">Code Quality & Debt Analysis</option>
                </select>
                <p className="text-[10px] text-muted-foreground mt-1.5">Reusable instruction sets for consistent team output.</p>
              </div>

              <div className="pt-2">
                <label className="flex items-start gap-3 p-3 border border-border rounded-xl bg-background/50 cursor-pointer hover:border-accent/30 transition-colors">
                  <div className="flex items-center h-5">
                    <input
                      type="checkbox"
                      className="w-4 h-4 rounded border-border text-accent focus:ring-accent/50"
                      checked={autoApprove}
                      onChange={(e) => setAutoApprove(e.target.checked)}
                    />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">Automated Approvals</span>
                    <span className="text-[10px] text-muted-foreground mt-0.5">Auto-approve trusted actions (e.g. data masking) to eliminate repetitive manual confirmation.</span>
                  </div>
                </label>
              </div>
            </div>
          </div>
          
          <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 flex items-start gap-3">
            <CheckCircle2 className="size-5 text-emerald-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-emerald-800 dark:text-emerald-400">Enterprise Ready</p>
              <p className="text-xs text-emerald-600/80 dark:text-emerald-400/80 mt-1">
                Your data is never used to train our base models. ISO 27001 & SOC2 Type II certified pipeline.
              </p>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}