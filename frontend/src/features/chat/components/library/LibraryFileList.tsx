import { LoaderCircle } from "lucide-react";

import { Badge } from "@/components/shadcn/badge";
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
                        <TableHead>ID</TableHead>
                        <TableHead>S3 Key</TableHead>
                        <TableHead>ファイル名</TableHead>
                        <TableHead>分類</TableHead>
                        <TableHead>ステータス</TableHead>
                        <TableHead>S3アップロード日時</TableHead>
                        <TableHead>RAG組み込み日時</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {files.map((file) => (
                        <TableRow key={file.id}>
                            <TableCell className="max-w-28 truncate font-mono text-[11px] text-[#6b7c75]">
                                {file.id}
                            </TableCell>
                            <TableCell className="max-w-52 truncate text-[#43584f]">
                                {file.s3Key}
                            </TableCell>
                            <TableCell className="max-w-40 truncate text-[#43584f]">
                                {file.name}
                            </TableCell>
                            <TableCell className="text-[#43584f]">
                                {file.category}
                            </TableCell>
                            <TableCell>
                                <Badge
                                    variant="outline"
                                    className="rounded-full border-[#dbe5df] bg-[#f5f8f6] text-[11px] text-[#567268]"
                                >
                                    {file.status}
                                </Badge>
                            </TableCell>
                            <TableCell className="text-[#6b7c75]">
                                {formatDate(file.s3UploadedAt)}
                            </TableCell>
                            <TableCell className="text-[#6b7c75]">
                                {file.ragIndexedAt
                                    ? formatDate(file.ragIndexedAt)
                                    : "-"}
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
        timeStyle: "short",
    }).format(new Date(value));
}
