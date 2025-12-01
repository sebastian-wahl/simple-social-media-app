import { useQuery } from "@tanstack/react-query";
import { listComments } from "../api/posts";

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
        <li key={c.id} className="bg-white p-3 rounded border">
          <div className="text-sm text-gray-500">
            {new Date(c.created_at).toLocaleString()} — {c.user}
          </div>
          <div>{c.text}</div>
        </li>
      ))}
    </ul>
  );
}