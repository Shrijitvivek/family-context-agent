/**
 * PageHeader
 *
 * Provides a consistent header for pages in the Family Context application.
 *
 * Responsibilities:
 * - Display the page title.
 * - Display an optional page description.
 * - Keep page headers visually consistent across the application.
 */

interface PageHeaderProps {
  title: string;
  description?: string;
}

export default function PageHeader({
  title,
  description,
}: PageHeaderProps) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
        {title}
      </h1>

      {description && (
        <p className="mt-2 max-w-2xl text-sm text-slate-500 sm:text-base">
          {description}
        </p>
      )}
    </div>
  );
}