import { Link } from "react-router-dom";
import type { PostReadDTO } from "../api/dto";
import RatingStars from "./RatingStars";

export default function PostCard({ post }: { post: PostReadDTO }) {
  const created = new Date(post.created_at).toLocaleString();
  const placeholderBase = "https://images.unsplash.com/photo-1520975916090-3105956dac38?q=80&w=1200&auto=format&fit=crop";
  const placeholder = '${placeholderBase}&seed=%{post.id}';
  const imgUrl = post.image_url || placeholder;

  return (
    <article className="bg-white rounded-lg shadow p-4 flex flex-col gap-3">
      <Link to={`/post/${post.id}`} className="block">
        <img
          src={imgUrl}
          alt={post.text}
          className="w-full h-64 object-cover rounded"
        />
      </Link>
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">{created}</div>
        <RatingStars value={post.toe_rating} readOnly size="sm" />
      </div>
      <h3 className="text-lg font-semibold">{post.text}</h3>
      <div className="text-sm text-gray-600">by {post.user}</div>
      <div className="flex flex-wrap gap-2">
        {post.tags.map((t) => (
          <span
            key={t}
            className="text-xs bg-gray-100 border border-gray-200 rounded px-2 py-0.5"
          >
            #{t}
          </span>
        ))}
      </div>
      <Link
        to={`/post/${post.id}`}
        className="text-blue-600 text-sm underline self-start"
      >
        View details & comments
      </Link>
    </article>
  );
}