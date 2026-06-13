import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { ChatComposer } from "@/features/chat/components/ChatComposer";

const defaultProps = {
    isContinuationExpired: false,
    isSending: false,
    message: "テストメッセージ",
    sendError: false,
    onMessageChange: vi.fn(),
    onSubmit: vi.fn(),
};

describe("ChatComposer", () => {
    test("IME変換中のEnterではメッセージを送信しない", () => {
        const onSubmit = vi.fn();
        render(<ChatComposer {...defaultProps} onSubmit={onSubmit} />);

        fireEvent.keyDown(
            screen.getByPlaceholderText("論文について質問する..."),
            {
                key: "Enter",
                isComposing: true,
            },
        );

        expect(onSubmit).not.toHaveBeenCalled();
    });

    test("IME変換中ではないEnterでメッセージを送信する", () => {
        const onSubmit = vi.fn();
        render(<ChatComposer {...defaultProps} onSubmit={onSubmit} />);

        fireEvent.keyDown(
            screen.getByPlaceholderText("論文について質問する..."),
            {
                key: "Enter",
                isComposing: false,
            },
        );

        expect(onSubmit).toHaveBeenCalledOnce();
    });

    test("ShiftとEnterの同時押下ではメッセージを送信しない", () => {
        const onSubmit = vi.fn();
        render(<ChatComposer {...defaultProps} onSubmit={onSubmit} />);

        fireEvent.keyDown(
            screen.getByPlaceholderText("論文について質問する..."),
            {
                key: "Enter",
                shiftKey: true,
            },
        );

        expect(onSubmit).not.toHaveBeenCalled();
    });

    test("継続期限切れの場合は入力と送信を無効化する", () => {
        const onSubmit = vi.fn();
        render(
            <ChatComposer
                {...defaultProps}
                isContinuationExpired
                onSubmit={onSubmit}
            />,
        );

        const textarea = screen.getByPlaceholderText("論文について質問する...");
        expect(textarea).toBeDisabled();
        expect(screen.getByRole("button", { name: "送信" })).toBeDisabled();
        expect(
            screen.getByText(/最終更新から24時間が経過したため/),
        ).toBeInTheDocument();

        fireEvent.keyDown(textarea, { key: "Enter" });
        expect(onSubmit).not.toHaveBeenCalled();
    });
});
