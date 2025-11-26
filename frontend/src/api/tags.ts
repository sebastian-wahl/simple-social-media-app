import { api } from "./client";
import type { TagReadDTO } from "./dto";

export async function listTags(): Promise<TagReadDTO[]> {
  const { data } = await api.get<TagReadDTO[]>("/tags");
  return data;
}