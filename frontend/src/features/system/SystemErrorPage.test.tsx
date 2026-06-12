import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { SystemErrorPage } from "@/features/system/SystemErrorPage";

test("システムエラー画面の主要メッセージを表示する", () => {
    render(<SystemErrorPage />);

    expect(
        screen.getByText("システム側で不具合が発生しています"),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "再読み込みする" }),
    ).toBeInTheDocument();
});

test("再読み込み操作を呼び出す", () => {
    const onReload = vi.fn();
    render(<SystemErrorPage onReload={onReload} />);

    screen.getByRole("button", { name: "再読み込みする" }).click();

    expect(onReload).toHaveBeenCalledOnce();
});
