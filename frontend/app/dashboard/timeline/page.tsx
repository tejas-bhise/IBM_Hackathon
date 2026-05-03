import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

export default function LegacyTimelineRedirect({
  searchParams,
}: {
  searchParams?: Record<string, string | string[] | undefined>;
}) {
  const projectIdParam = searchParams?.project_id;
  const projectId = Array.isArray(projectIdParam) ? projectIdParam[0] : projectIdParam;
  redirect(projectId ? `/dashboard?project_id=${encodeURIComponent(projectId)}` : '/dashboard');
}
