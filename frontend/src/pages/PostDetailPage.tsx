import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getPost } from "../api/posts";
import CommentList from "../components/CommentList";
import CommentForm from "../components/CommentForm";
import RatingStars from "../components/RatingStars";

export default function PostDetailPage() {
  const { id } = useParams();
  const postId = Number(id);

  const { data: post, isLoading } = useQuery({
    queryKey: ["post", postId],
    queryFn: () => getPost(postId),
    enabled: Number.isFinite(postId),
  });

  if (!Number.isFinite(postId)) return <div>Invalid post id.</div>;
  if (isLoading) return <div>Loading…</div>;
  if (!post) return <div>Post not found.</div>;

  const placeholderBase =
    "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1600&auto=format&fit=crop";
  const placeholder = `${placeholderBase}&seed=${post.id}`;

  const imgUrl = post.image_url
    ? `${import.meta.env.VITE_API_BASE_URL}/images/${post.image_url}`
    : placeholder;

  return (
  <div className="space-y-4">
    {/* IMAGE */}
    <div className="bg-white rounded shadow p-4">
      <img
        src={imgUrl}
        alt={post.text}
        className="w-full rounded mb-4"
      />

      <div className="flex justify-between items-start gap-4">
        {/* LEFT */}
        <div className="space-y-1">
          <h2 className="text-xl font-semibold">{post.text}</h2>
          <div className="text-sm text-gray-500">
            {new Date(post.created_at).toLocaleString()} — by {post.user}
          </div>
          <div className="mt-2 flex gap-2 flex-wrap">
            {post.tags.map((t) => (
              <span
                key={t}
                className="text-xs bg-gray-100 border px-2 py-0.5 rounded"
              >
                #{t}
              </span>
            ))}
          </div>
        </div>

        {/* RIGHT */}
        <div className="flex flex-col items-end">
          <RatingStars value={post.rating} readOnly />
          <div className="text-sm text-gray-600 mt-1">
            {post.rating.toFixed(2)} / 5
          </div>
        </div>
      </div>
    </div>

    {/* COMMENTS */}
    <section className="space-y-3">
      <h3 className="text-lg font-semibold">Comments</h3>
      <CommentForm postId={postId} />
      <CommentList postId={postId} />
    </section>
  </div>
);
}
