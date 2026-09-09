export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-subtext text-sm">
      <div className="animate-pulse">{label}</div>
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-border rounded-lg bg-surface">
      <p className="text-sm font-medium text-text">{title}</p>
      {description && <p className="mt-1 text-sm text-subtext max-w-sm">{description}</p>}
    </div>
  );
}

export function ErrorState({ message = "Something went wrong. Please try again." }: { message?: string }) {
  return (
    <div className="flex items-center justify-center py-16 text-center">
      <p className="text-sm text-danger">{message}</p>
    </div>
  );
}
