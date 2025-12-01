import { useMutation, useQueryClient } from "@tanstack/react-query";
import { addComment } from "../api/posts";
import { useState } from "react";

export default function CommentForm({ postId }: { postId: number }) {
  const qc = useQueryClient();
  const [user, setUser] = useState("");
  const [text, setText] = useState("");

  const mutation = useMutation({
    mutationFn: () => addComment(postId, { user, text }),
    onSuccess: () => {
      setText("");
      qc.invalidateQueries({ queryKey: ["comments", postId] });
    },
  });

  return (
    <form
      className="bg-white p-3 rounded border flex flex-col gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        if (!user || !text) return;
        mutation.mutate();
      }}
    >
      <input
        className="border rounded px-2 py-1"
        placeholder="Your name"
        value={user}
        onChange={(e) => setUser(e.target.value)}
      />
      <textarea
        className="border rounded px-2 py-1"
        placeholder="Write a comment…"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button
        type="submit"
        className="self-end bg-blue-600 text-white px-3 py-1 rounded"
        disabled={mutation.isPending}
      >
        {mutation.isPending ? "Posting…" : "Post comment"}
      </button>
    </form>
  );
}