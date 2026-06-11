import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { SystemErrorScreen } from "./SystemErrorScreen";

test("システム側の不具合であることと利用者向けの対応方法を表示する", () => {
    render(<SystemErrorScreen />);

    expect(
        screen.getByRole("heading", {
            name: "システム側で不具合が発生しています",
        }),
    ).toBeInTheDocument();
    expect(
        screen.getByText(
            /お客様の操作やアカウントに問題がある状態ではありません/,
        ),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/時間を置いてから再読み込みしてください/),
    ).toBeInTheDocument();
});

test("再読み込みボタンから指定された処理を実行する", () => {
    const onReload = vi.fn();
    render(<SystemErrorScreen onReload={onReload} />);

    fireEvent.click(screen.getByRole("button", { name: "再読み込みする" }));

    expect(onReload).toHaveBeenCalledOnce();
});
