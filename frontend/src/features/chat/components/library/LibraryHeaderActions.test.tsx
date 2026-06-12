import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { LibraryHeaderActions } from "@/features/chat/components/library/LibraryHeaderActions";
import { getIndexedFiles } from "@/lib/library-api";

vi.mock("@/lib/library-api", () => ({
    getIndexedFiles: vi.fn(),
}));

describe("LibraryHeaderActions", () => {
    beforeEach(() => {
        vi.mocked(getIndexedFiles).mockReset();
    });

    test("取り込み済みファイル一覧を取得して件数を表示する", async () => {
        vi.mocked(getIndexedFiles).mockResolvedValue([
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
        ]);

        render(<LibraryHeaderActions />);

        await waitFor(() => {
            expect(getIndexedFiles).toHaveBeenCalledOnce();
        });
        expect(screen.getByText("2 papers indexed")).toBeInTheDocument();
    });

    test("ライブラリを開いて空状態を表示する", async () => {
        vi.mocked(getIndexedFiles).mockResolvedValue([]);
        render(<LibraryHeaderActions />);

        await screen.findByText("0 papers indexed");
        fireEvent.click(screen.getByRole("button", { name: "ライブラリ" }));

        expect(
            screen.getByText("RAGへ取り込み済みのファイルはありません。"),
        ).toBeInTheDocument();
    });
});
