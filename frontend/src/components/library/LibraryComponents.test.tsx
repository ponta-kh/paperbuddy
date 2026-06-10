import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { IndexedPaperCount } from "./IndexedPaperCount";
import { LibraryButton } from "./LibraryButton";
import { LibraryFileList } from "./LibraryFileList";

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
                        name: "paper-a.pdf",
                        category: "LLM",
                        status: "indexed",
                        s3UploadedAt: "2026-01-01T00:00:00Z",
                        ragIndexedAt: "2026-01-02T00:00:00Z",
                    },
                    {
                        id: "00000000-0000-0000-0000-000000000002",
                        s3Key: "papers/b.pdf",
                        name: "paper-b.pdf",
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

        expect(screen.getByText("ID")).toBeInTheDocument();
        expect(screen.getByText("S3 Key")).toBeInTheDocument();
        expect(screen.getByText("papers/a.pdf")).toBeInTheDocument();
        expect(screen.getByText("papers/b.pdf")).toBeInTheDocument();
        expect(screen.getByText("paper-a.pdf")).toBeInTheDocument();
        expect(screen.getByText("paper-b.pdf")).toBeInTheDocument();
        expect(screen.getByText("LLM")).toBeInTheDocument();
        expect(screen.getByText("processing")).toBeInTheDocument();
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
