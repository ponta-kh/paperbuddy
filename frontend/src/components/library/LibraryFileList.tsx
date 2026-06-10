import { FileText, LoaderCircle } from "lucide-react";

import type { IndexedFile } from "@/lib/library-api";

type LibraryFileListProps = {
    files: IndexedFile[];
    isLoading: boolean;
    loadError: boolean;
};

export function LibraryFileList({
    files,
    isLoading,
    loadError,
}: LibraryFileListProps) {
    if (isLoading) {
        return (
            <div className="flex items-center gap-2 px-4 py-6 text-sm text-[#74837d]">
                <LoaderCircle className="size-4 animate-spin" />
                取り込み済みファイルを読み込んでいます
            </div>
        );
    }

    if (loadError) {
        return (
            <p className="px-4 py-6 text-sm text-destructive">
                取り込み済みファイルを取得できませんでした。
            </p>
        );
    }

    if (files.length === 0) {
        return (
            <p className="px-4 py-6 text-sm text-[#74837d]">
                RAGへ取り込み済みのファイルはありません。
            </p>
        );
    }

    return (
        <ul className="space-y-1 px-3 py-4">
            {files.map((file) => (
                <li
                    key={file.name}
                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-[#43584f]"
                >
                    <FileText className="size-4 shrink-0 text-[#6f847b]" />
                    <span className="truncate">{file.name}</span>
                </li>
            ))}
        </ul>
    );
}
