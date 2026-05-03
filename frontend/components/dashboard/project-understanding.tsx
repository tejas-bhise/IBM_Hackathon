'use client';



interface ProjectUnderstandingProps {
  name: string;
  type: string;
  modules: string[];
  dataFlow: string;
}

export function ProjectUnderstanding({ name, type, modules, dataFlow }: ProjectUnderstandingProps) {
  return (
    <div className="h-full flex flex-col mb-4">
      <h3 className="text-xl font-bold text-foreground mb-6">Project overview</h3>

      <div className="space-y-6 flex-1">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-foreground text-base leading-none">•</span>
            <label className="text-sm font-semibold text-muted-foreground">Project Type</label>
          </div>
          <p className="text-sm text-foreground ml-4">{type}</p>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-foreground text-base leading-none">•</span>
            <label className="text-sm font-semibold text-muted-foreground">Key Modules</label>
          </div>
          <div className="flex flex-wrap gap-2 ml-4">
            {modules.map((module, idx) => (
              <div key={idx} className="inline-block bg-secondary px-3 py-1.5 rounded-md text-xs font-medium text-foreground border border-border/60 hover:border-accent/40 transition-colors">
                {module}
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-foreground text-base leading-none">•</span>
            <label className="text-sm font-semibold text-muted-foreground">Data Flow</label>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed ml-4">{dataFlow}</p>
        </div>
      </div>

      <div className="mt-6">
        <p className="text-xs text-muted-foreground">
          <span className="font-semibold text-foreground">Tip:</span> Keep data flows secure by validating inputs at every layer.
        </p>
      </div>
    </div>
  );
}
