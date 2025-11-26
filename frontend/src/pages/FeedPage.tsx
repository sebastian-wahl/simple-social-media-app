import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { keepPreviousData } from "@tanstack/react-query";
import { listPosts } from "../api/posts";
import PostCard from "../components/PostCard"
import TagFilter from "../components/TagFilter";
import RatingStars from "../components/RatingStars";

export default function FeedPage() {
  const [q, setQ] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [matchAll, setMatchAll] = useState(false);
  const [minRating, setMinRating] = useState<number | undefined>(undefined);
  const [orderBy, setOrderBy] =
    useState<"relevance" | "newest" | "rating">("relevance");
  const [page, setPage] = useState(0);
  const limit = 10;

  const params = useMemo(
    () => ({
      q: q || undefined,
      tags: tags.length ? tags : undefined,
      match_all: matchAll || undefined,
      min_rating: minRating,
      limit,
      offset: page * limit,
      order_by: orderBy,
    }),
    [q, tags, matchAll, minRating, page, orderBy]
  );

  const { data, isLoading } = useQuery({

queryKey: ["posts", params],

queryFn: () => listPosts(params),

placeholderData: keepPreviousData,
});

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow flex flex-wrap gap-3 items-center">
        <input
          className="border rounded px-3 py-1 flex-1 min-w-56"
          placeholder="Search user or text…"
          value={q}
          onChange={(e) => {
            setPage(0);
            setQ(e.target.value);
          }}
        />
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Min Rating:</span>
          <RatingStars
            value={minRating ?? 0}
            onChange={(v) => {
              setPage(0);
              setMinRating(v);
            }}
          />
        </div>
        <select
          className="border rounded px-2 py-1"
          value={orderBy}
          onChange={(e) => setOrderBy(e.target.value as any)}
        >
          <option value="relevance">Most relevant</option>
          <option value="newest">Newest</option>
          <option value="rating">Highest rated</option>
        </select>
      </div>

      <TagFilter
        selected={tags}
        setSelected={(t) => {
          setPage(0);
          setTags(t);
        }}
        matchAll={matchAll}
        setMatchAll={setMatchAll}
      />

      {isLoading && <div>Loading feed…</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data?.items.map((p) => (
          <PostCard key={p.id} post={p} />
        ))}
      </div>

      <div className="flex items-center justify-center gap-3">
        <button
          className="px-3 py-1 rounded border"
          disabled={page === 0}
          onClick={() => setPage((p) => Math.max(0, p - 1))}
        >
          Prev
        </button>
        <span className="text-sm">
          {page * limit + 1}-
          {Math.min((page + 1) * limit, data?.meta.total ?? 0)} /{" "}
          {data?.meta.total ?? 0}
        </span>
        <button
          className="px-3 py-1 rounded border"
          disabled={(data?.items.length ?? 0) < limit}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}