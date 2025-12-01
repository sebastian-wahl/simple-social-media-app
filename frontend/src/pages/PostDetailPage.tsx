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

  const isAbsolute =
    post.image_path.startsWith("http://") ||
    post.image_path.startsWith("https://") ||
    post.image_path.startsWith("/");

  const placeholderBase =
    "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1600&auto=format&fit=crop";
  const placeholder = `${placeholderBase}&seed=${post.id}`;

  const imgUrl = isAbsolute ? post.image_path : placeholder;

  return (
    <div className="space-y-4">
      <div className="bg-white rounded shadow p-4">
        <img src={imgUrl} alt={post.text} className="w-full rounded mb-3" />
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">{post.text}</h2>
          <RatingStars value={post.toe_rating} readOnly />
        </div>
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

      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Comments</h3>
        <CommentForm postId={postId} />
        <CommentList postId={postId} />
      </section>
    </div>
  );
}