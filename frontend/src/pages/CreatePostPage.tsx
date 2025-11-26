import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createPost, uploadImage } from "../api/posts";
import { useState } from "react";
import RatingStars from "../components/RatingStars";
import { useNavigate } from "react-router-dom";

export default function CreatePostPage() {
  const [file, setFile] = useState<File | null>(null);
  const [imagePath, setImagePath] = useState<string | null>(null);
  const [user, setUser] = useState("");
  const [text, setText] = useState("");
  const [rating, setRating] = useState(3);
  const [tags, setTags] = useState("");

  const navigate = useNavigate();
  const qc = useQueryClient();

  const uploadMut = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("No file selected");
      const res = await uploadImage(file);
      setImagePath(res.image_path);
      return res;
    },
  });

  const createMut = useMutation({
    mutationFn: async () => {
      if (!imagePath) throw new Error("Upload an image first");
      const payload = {
        image_path: imagePath,
        text,
        user,
        toe_rating: rating,
        tags: tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      };
      return await createPost(payload);
    },
    onSuccess: (post) => {
      qc.invalidateQueries({ queryKey: ["posts"] });
      navigate(`/post/${post.id}`);
    },
  });

  return (
    <div className="max-w-xl mx-auto space-y-4 bg-white p-4 rounded shadow">
      <h2 className="text-xl font-semibold">Create Post</h2>

      <div className="space-y-2">
        <label className="block text-sm">Image</label>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button
          onClick={() => uploadMut.mutate()}
          className="bg-gray-800 text-white px-3 py-1 rounded"
          disabled={!file || uploadMut.isPending}
        >
          {uploadMut.isPending ? "Uploading…" : "Upload"}
        </button>
        {imagePath && (
          <div className="text-green-700 text-sm">
            Uploaded. image_path: {imagePath}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <label className="block text-sm">User</label>
        <input
          className="border rounded w-full px-3 py-1"
          value={user}
          onChange={(e) => setUser(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm">Text</label>
        <textarea
          className="border rounded w-full px-3 py-1"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <label className="block text-sm">Toe Rating</label>
        <RatingStars value={rating} onChange={setRating} />
      </div>

      <div className="space-y-2">
        <label className="block text-sm">Tags (comma-separated)</label>
        <input
          className="border rounded w-full px-3 py-1"
          placeholder="blue, common"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
        />
      </div>

      <button
        disabled={createMut.isPending}
        onClick={() => createMut.mutate()}
        className="bg-blue-600 text-white px-4 py-2 rounded"
      >
        {createMut.isPending ? "Creating…" : "Create Post"}
      </button>
    </div>
  );
}