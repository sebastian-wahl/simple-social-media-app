import { api } from "./client";
import type {
  CommentCreateDTO,
  CommentReadDTO,
  PostCreateDTO,
  PostPageDTO,
  PostReadDTO,
  UploadImageResponseDTO,
} from "./dto";

export async function listPosts(params: {
  q?: string;
  tags?: string[];
  match_all?: boolean;
  min_rating?: number;
  max_rating?: number;
  limit?: number;
  offset?: number;
  order_by?: "relevance" | "newest" | "rating";
}): Promise<PostPageDTO> {
  const { data } = await api.get<PostPageDTO>("/posts", { params });
  return data;
}

export async function getPost(id: number): Promise<PostReadDTO> {
  const { data } = await api.get<PostReadDTO>(`/posts/${id}`);
  return data;
}

export async function listComments(postId: number): Promise<CommentReadDTO[]> {
  const { data } = await api.get<CommentReadDTO[]>(
    `/posts/${postId}/comments`,
  );
  return data;
}

export async function addComment(
  postId: number,
  payload: CommentCreateDTO,
): Promise<CommentReadDTO> {
  const { data } = await api.post<CommentReadDTO>(
    `/posts/${postId}/comments`,
    payload,
  );
  return data;
}

export async function uploadImage(file: File): Promise<UploadImageResponseDTO> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<UploadImageResponseDTO>(
    "/uploads/images",
    form,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

export async function createPost(payload: PostCreateDTO): Promise<PostReadDTO> {
  const { data } = await api.post<PostReadDTO>("/posts", payload);
  return data;
}