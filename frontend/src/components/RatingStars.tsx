type Props = {
  value: number;
  onChange?: (v: number) => void;
  size?: "sm" | "md";
  readOnly?: boolean;
};

export default function RatingStars({
  value,
  onChange,
  size = "md",
  readOnly = false,
}: Props) {
  const sz = size === "sm" ? "text-xl" : "text-2xl";
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          disabled={readOnly}
          onClick={() => onChange?.(n)}
          className={`${sz} ${n <= value ? "text-yellow-500" : "text-gray-300"}`}
          aria-label={`rating ${n}`}
        >
          ★
        </button>
      ))}
    </div>
  );
}