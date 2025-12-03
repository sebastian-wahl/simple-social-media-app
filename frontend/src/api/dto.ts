export interface PostReadDTO {
    id: number;
    image_path: string;
    image_url: string;
    text: string;
    user: string;
    toe_rating: number;
    created_at: string;
    tags: string[];
}

export interface PageMetaDTO {
    total: number;
    limit: number;
    offset: number;
}

export interface PostPageDTO {
    items: PostReadDTO[];
    meta: PageMetaDTO;
}

export interface TagReadDTO {
    id: number;
    name: string;
    count: number;
}

export interface CommentReadDTO {
    id: number;
    post_id: number;
    user: string;
    text: string;
    created_at: string;
}

export interface PostCreateDTO {
    image_path: string;
    text: string;
    user: string;
    toe_rating: number;
    tags: string[];
}

export interface CommentCreateDTO {
    user: string;
    text: string;
}

export interface UploadImageResponseDTO {
    image_path: string;
}