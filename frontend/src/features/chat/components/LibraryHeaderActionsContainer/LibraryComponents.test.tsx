import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { IndexedPaperCount } from "@/features/chat/components/LibraryHeaderActionsContainer/IndexedPaperCount";
import { LibraryButton } from "@/features/chat/components/LibraryHeaderActionsContainer/LibraryButton";
import { LibraryFileList } from "@/features/chat/components/LibraryHeaderActionsContainer/LibraryFileList";

describe("IndexedPaperCount", () => {
    test("取り込み済みファイル件数を表示する", () => {
        render(
            <IndexedPaperCount count={2} isLoading={false} loadError={false} />,
        );

        expect(screen.getByText("2 papers indexed")).toBeInTheDocument();
    });
});

describe("LibraryButton", () => {
    test("クリック時に通知する", () => {
        const onClick = vi.fn();
        render(<LibraryButton onClick={onClick} />);

        fireEvent.click(screen.getByRole("button", { name: "ライブラリ" }));

        expect(onClick).toHaveBeenCalledOnce();
    });
});

describe("LibraryFileList", () => {
    test("取り込み済みファイルを表示する", () => {
        render(
            <LibraryFileList
                files={[
                    {
                        id: "00000000-0000-0000-0000-000000000001",
                        s3Key: "papers/a.pdf",
                        name: "paper-a",
                        category: "LLM",
                        status: "indexed",
                        s3UploadedAt: "2026-01-01T00:00:00Z",
                        ragIndexedAt: "2026-01-02T00:00:00Z",
                    },
                    {
                        id: "00000000-0000-0000-0000-000000000002",
                        s3Key: "papers/b.pdf",
                        name: "paper-b",
                        category: "経済",
                        status: "processing",
                        s3UploadedAt: "2026-01-03T00:00:00Z",
                        ragIndexedAt: null,
                    },
                ]}
                isLoading={false}
                loadError={false}
            />,
        );

        expect(screen.getByText("論文名")).toBeInTheDocument();
        expect(screen.getByText("分類")).toBeInTheDocument();
        expect(screen.getByText("アップロード日")).toBeInTheDocument();
        expect(screen.getByText("paper-a")).toBeInTheDocument();
        expect(screen.getByText("paper-b")).toBeInTheDocument();
        expect(screen.getByText("LLM")).toBeInTheDocument();
        expect(screen.getByText("経済")).toBeInTheDocument();
        expect(screen.queryByText("ID")).not.toBeInTheDocument();
        expect(screen.queryByText("S3 Key")).not.toBeInTheDocument();
        expect(screen.queryByText("papers/a.pdf")).not.toBeInTheDocument();
        expect(screen.queryByText("paper-a.pdf")).not.toBeInTheDocument();
        expect(screen.queryByText("processing")).not.toBeInTheDocument();
    });

    test("空一覧の場合は空状態を表示する", () => {
        render(
            <LibraryFileList files={[]} isLoading={false} loadError={false} />,
        );

        expect(
            screen.getByText("RAGへ取り込み済みのファイルはありません。"),
        ).toBeInTheDocument();
    });
});
