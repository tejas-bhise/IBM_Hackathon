'use client';

import { useState } from 'react';

interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  category: string;
  file?: string;
  author?: string;
}

interface MemoryTimelineProps {
  events: TimelineEvent[];
}

export function MemoryTimeline({ events = [] }: MemoryTimelineProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // ✅ FIX: filter out null/undefined/empty before calling .charAt()
  const rawCategories = Array.from(
    new Set(events.map((e) => e?.category).filter((c): c is string => typeof c === 'string' && c.trim() !== ''))
  );
  const categories = ['all', ...rawCategories];

  const categoryCounts = rawCategories.reduce<Record<string, number>>((acc, cat) => {
    acc[cat] = events.filter((e) => e?.category === cat).length;
    return acc;
  }, {});

  const filteredEvents =
    selectedCategory === 'all'
      ? events.filter((e) => e != null)
      : events.filter((e) => e?.category === selectedCategory);

  const formatTimestamp = (ts: string) => {
    if (!ts) return '';
    try {
      return new Date(ts).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  const getCategoryColor = (cat: string) => {
    const colors: Record<string, string> = {
      feature:   'bg-blue-500/10 text-blue-400 border-blue-500/20',
      security:  'bg-red-500/10 text-red-400 border-red-500/20',
      refactor:  'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
      fix:       'bg-orange-500/10 text-orange-400 border-orange-500/20',
      test:      'bg-green-500/10 text-green-400 border-green-500/20',
      deploy:    'bg-purple-500/10 text-purple-400 border-purple-500/20',
    };
    return colors[cat?.toLowerCase()] ?? 'bg-secondary text-muted-foreground border-border';
  };

  const getDotColor = (cat: string) => {
    const dots: Record<string, string> = {
      feature:  'bg-blue-500',
      security: 'bg-red-500',
      refactor: 'bg-yellow-500',
      fix:      'bg-orange-500',
      test:     'bg-green-500',
      deploy:   'bg-purple-500',
    };
    return dots[cat?.toLowerCase()] ?? 'bg-accent';
  };

  return (
    <div className="space-y-6">
      {/* Category filter tabs */}
      <div className="flex flex-wrap gap-2">
        {categories
          .filter((category): category is string => typeof category === 'string')  // ✅ runtime safety guard
          .map((category) => {
            const count = category === 'all' ? events.length : (categoryCounts[category] ?? 0);
            const label =
              category === 'all'
                ? 'All Events'
                : category.charAt(0).toUpperCase() + category.slice(1); // ✅ safe now

            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  selectedCategory === category
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-border bg-secondary/50 text-muted-foreground hover:bg-secondary hover:text-foreground'
                }`}
              >
                {label}
                <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold ${
                  selectedCategory === category ? 'bg-accent/20' : 'bg-border'
                }`}>
                  {count}
                </span>
              </button>
            );
          })}
      </div>

      {/* Timeline */}
      {filteredEvents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-3 text-4xl">🗂️</div>
          <h3 className="text-base font-semibold">No events yet</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Memory events will appear here once analysis is complete.
          </p>
        </div>
      ) : (
        <div className="relative space-y-4">
          {/* Vertical line */}
          <div className="absolute left-3.5 top-0 bottom-0 w-px bg-border" />

          {filteredEvents.map((event) => {
            if (!event) return null;
            return (
              <div key={event.id ?? Math.random()} className="relative flex gap-4 pl-10">
                {/* Dot */}
                <div className={`absolute left-2 top-2 h-3 w-3 rounded-full border-2 border-background ${getDotColor(event.category)}`} />

                <div className="flex-1 rounded-xl border border-border bg-card p-4">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${getCategoryColor(event.category)}`}>
                      {event.category
                        ? event.category.charAt(0).toUpperCase() + event.category.slice(1)
                        : 'Other'}
                    </span>
                    {event.timestamp && (
                      <span className="text-xs text-muted-foreground">
                        {formatTimestamp(event.timestamp)}
                      </span>
                    )}
                    {event.author && (
                      <span className="text-xs text-muted-foreground">· {event.author}</span>
                    )}
                  </div>

                  <p className="text-sm font-medium">{event.title}</p>

                  {event.description && event.description !== event.title && (
                    <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                      {event.description}
                    </p>
                  )}

                  {event.file && (
                    <p className="mt-2 font-mono text-[10px] text-muted-foreground">
                      📄 {event.file}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}