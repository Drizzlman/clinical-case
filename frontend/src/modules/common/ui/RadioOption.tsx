import type { FC } from "react";

type RadioTone = "default" | "correct" | "incorrect";

const TONE_CLASSES: Record<RadioTone, string> = {
  default: "border-transparent hover:bg-slate-50",
  correct: "border-emerald-400 bg-emerald-50",
  incorrect: "border-red-400 bg-red-50",
};

interface RadioOptionProps {
  name: string;
  value: number;
  label: string;
  checked: boolean;
  disabled?: boolean;
  tone?: RadioTone;
  statusLabel?: string;
  onSelect: (value: number) => void;
}

export const RadioOption: FC<RadioOptionProps> = ({
  name,
  value,
  label,
  checked,
  disabled = false,
  tone = "default",
  statusLabel,
  onSelect,
}) => {
  const statusColor = tone === "incorrect" ? "text-red-700" : "text-emerald-700";
  return (
    <label
      className={`flex items-center gap-3 rounded-md border px-2 py-2 ${
        disabled ? "cursor-default" : "cursor-pointer"
      } ${TONE_CLASSES[tone]}`}
    >
      <input
        type="radio"
        name={name}
        value={value}
        checked={checked}
        disabled={disabled}
        onChange={() => onSelect(value)}
      />
      <span>{label}</span>
      {statusLabel ? (
        <span className={`ml-auto text-xs font-medium ${statusColor}`}>{statusLabel}</span>
      ) : null}
    </label>
  );
};
