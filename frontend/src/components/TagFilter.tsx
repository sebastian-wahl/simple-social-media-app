import { useQuery } from "@tanstack/react-query";
import { listTags } from "../api/tags";

export default function TagFilter({
  selected,
  setSelected,
  matchAll,
  setMatchAll,
}: {
  selected: string[];
  setSelected: (tags: string[]) => void;
  matchAll: boolean;
  setMatchAll: (v: boolean) => void;
}) {
  const { data, isLoading } = useQuery({
    queryKey: ["tags"],
    queryFn: listTags,
  });

  const toggle = (name: string) => {
    if (selected.includes(name)) {
      setSelected(selected.filter((t) => t !== name));
    } else {
      setSelected([...selected, name]);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow flex flex-wrap gap-2 items-center">
      <span className="font-semibold mr-2">Tags:</span>
      {isLoading && <span>Loading…</span>}
      {data?.map((t) => (
        <button
          key={t.id}
          onClick={() => toggle(t.name)}
          className={`px-2 py-1 rounded border ${
            selected.includes(t.name)
              ? "bg-blue-600 text-white border-blue-600"
              : "bg-white border-gray-300"
          }`}
        >
          #{t.name} ({t.count})
        </button>
      ))}
      <label className="ml-auto text-sm flex items-center gap-2">
        <input
          type="checkbox"
          checked={matchAll}
          onChange={(e) => setMatchAll(e.target.checked)}
        />
        Match all
      </label>
    </div>
  );
}