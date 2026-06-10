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
                files={[{ name: "paper-a.pdf" }, { name: "paper-b.pdf" }]}
                isLoading={false}
                loadError={false}
            />,
        );

        expect(screen.getByText("paper-a.pdf")).toBeInTheDocument();
        expect(screen.getByText("paper-b.pdf")).toBeInTheDocument();
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
