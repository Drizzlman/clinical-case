import type { FC } from "react";

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
}

export const ProgressBar: FC<ProgressBarProps> = ({ value, max = 100, label = "Progress" }) => {
  const percentage = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuenow={Math.round(percentage)}
      aria-valuemin={0}
      aria-valuemax={100}
      className="h-2 w-full overflow-hidden rounded-full bg-slate-200"
    >
      <div
        className="h-full rounded-full bg-slate-900 transition-all"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};
