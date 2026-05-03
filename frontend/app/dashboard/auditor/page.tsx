import { Suspense } from 'react';
import AuditorContent from './AuditorContent';

export default function AuditorPage() {
  return (
    <Suspense fallback={
      <div className="p-4 lg:p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Security & Privacy Auditor</h1>
            <p className="text-muted-foreground">Detailed analysis of all detected security issues and sensitive data in your codebase</p>
          </div>
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
              <p className="text-muted-foreground">Running security analysis...</p>
            </div>
          </div>
        </div>
      </div>
    }>
      <AuditorContent />
    </Suspense>
  );
}
