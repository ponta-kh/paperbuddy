import { LoaderCircle } from "lucide-react";

import { SearchEmptyState } from "@/components/SearchEmptyState";
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
            <SearchEmptyState
                message="RAGへ取り込み済みのファイルはありません。"
                className="px-4 py-6 text-sm"
            />
        );
    }

    return (
        <div className="px-3 py-4">
            <Table className="table-fixed">
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[58%]">論文名</TableHead>
                        <TableHead className="w-[18%]">分類</TableHead>
                        <TableHead className="w-[24%]">
                            アップロード日
                        </TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {files.map((file) => (
                        <TableRow key={file.id}>
                            <TableCell className="whitespace-normal break-words text-[#43584f]">
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
