import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { ChatComposer } from "@/features/chat/components/ChatComposer";

const defaultProps = {
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
});
