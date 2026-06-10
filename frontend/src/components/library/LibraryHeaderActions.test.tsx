import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { getIndexedFiles } from "@/lib/library-api";
import { LibraryHeaderActions } from "./LibraryHeaderActions";

vi.mock("@/lib/library-api", () => ({
    getIndexedFiles: vi.fn(),
}));

describe("LibraryHeaderActions", () => {
    beforeEach(() => {
        vi.mocked(getIndexedFiles).mockReset();
    });

    test("取り込み済みファイル一覧を取得して件数を表示する", async () => {
        vi.mocked(getIndexedFiles).mockResolvedValue([
            { name: "paper-a.pdf" },
            { name: "paper-b.pdf" },
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
