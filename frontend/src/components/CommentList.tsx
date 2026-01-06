import { useQuery } from "@tanstack/react-query";
import { listComments } from "../api/posts";

function sentimentBadge(
  sentiment?: "negative" | "neutral" | "positive",
  score?: number,
) {
  if (!sentiment) {
    return {
      label: "Analyzing…",
      emoji: "⏳",
      className: "bg-gray-100 text-gray-600",
    };
  }

  const confidence = score ? ` (${(score * 100).toFixed(0)}%)` : "";

  switch (sentiment) {
    case "negative":
      return {
        label: `Negative${confidence}`,
        emoji: "😕",
        className: "bg-red-100 text-red-800",
      };
    case "neutral":
      return {
        label: `Neutral${confidence}`,
        emoji: "😐",
        className: "bg-gray-100 text-gray-700",
      };
    case "positive":
      return {
        label: `Positive${confidence}`,
        emoji: "😊",
        className: "bg-green-100 text-green-800",
      };
  }
}


export default function CommentList({ postId }: { postId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["comments", postId],
    queryFn: () => listComments(postId),
  });

  if (isLoading) return <div>Loading comments…</div>;
  if (!data || data.length === 0) return <div>No comments yet.</div>;

  return (
    <ul className="space-y-3">
      {data.map((c) => (
        <li key={c.id} className="bg-white p-3 rounded border space-y-1">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <span>
              {new Date(c.created_at).toLocaleString()} — {c.user}
            </span>

            {(() => {
              const s = sentimentBadge(c.sentiment, c.sentiment_score);
              return (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 ${s.className}`}
                  title={s.label}
                >
                  <span>{s.emoji}</span>
                  <span className="hidden sm:inline">{s.label}</span>
                </span>
              );
            })()}
          </div>

          <div className="text-gray-900">{c.text}</div>
        </li>

      ))}
    </ul>
  );
}