import { lazy, Suspense } from 'react';

const UrlImportFlow = lazy(() => import('@/features/new-reading/UrlImportFlow'));

export default function NewReadingUrl() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100dvh', background: 'var(--stage)' }} />}>
      <UrlImportFlow />
    </Suspense>
  );
}
