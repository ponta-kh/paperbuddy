import { LoaderCircle } from "lucide-react";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/shadcn/table";
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
        <div className="px-3 py-4">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>PDF名称</TableHead>
                        <TableHead>分類</TableHead>
                        <TableHead>アップロード日</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {files.map((file) => (
                        <TableRow key={file.id}>
                            <TableCell className="max-w-80 truncate text-[#43584f]">
                                {file.name}
                            </TableCell>
                            <TableCell className="text-[#43584f]">
                                {file.category}
                            </TableCell>
                            <TableCell className="text-[#6b7c75]">
                                {formatDate(file.s3UploadedAt)}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

function formatDate(value: string) {
    return new Intl.DateTimeFormat("ja-JP", {
        dateStyle: "medium",
    }).format(new Date(value));
}
