import { LoaderCircle, Sparkles } from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import { ScrollArea } from "@/components/shadcn/scroll-area";
import { suggestions } from "@/features/chat/utils/chat-data";
import type { ChatMessage } from "@/lib/chat-api";

const STICK_TO_BOTTOM_THRESHOLD_PX = 80;

type ChatConversationProps = {
    isLoading: boolean;
    isSending: boolean;
    loadError: boolean;
    messages: ChatMessage[];
    onSuggestionSelect: (suggestion: string) => void;
};

export function ChatConversation({
    isLoading,
    isSending,
    loadError,
    messages,
    onSuggestionSelect,
}: ChatConversationProps) {
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const shouldStickToBottomRef = useRef(true);

    const getViewport = useCallback(
        () =>
            scrollAreaRef.current?.querySelector<HTMLElement>(
                "[data-slot='scroll-area-viewport']",
            ),
        [],
    );

    useEffect(() => {
        const viewport = getViewport();
        if (!viewport) return;

        const updateStickToBottom = () => {
            const distanceFromBottom =
                viewport.scrollHeight -
                viewport.scrollTop -
                viewport.clientHeight;
            shouldStickToBottomRef.current =
                distanceFromBottom < STICK_TO_BOTTOM_THRESHOLD_PX;
        };

        updateStickToBottom();
        viewport.addEventListener("scroll", updateStickToBottom, {
            passive: true,
        });
        return () =>
            viewport.removeEventListener("scroll", updateStickToBottom);
    }, [getViewport]);

    useLayoutEffect(() => {
        if (!shouldStickToBottomRef.current) return;

        const viewport = getViewport();
        if (!viewport) return;

        if (typeof viewport.scrollTo === "function") {
            viewport.scrollTo({
                top: viewport.scrollHeight,
                behavior: "smooth",
            });
            return;
        }

        viewport.scrollTop = viewport.scrollHeight;
    });

    return (
        <ScrollArea ref={scrollAreaRef} className="min-h-0 flex-1">
            <div className="mx-auto w-full max-w-3xl px-4 pb-8 pt-8 sm:px-8 sm:pb-10 sm:pt-12">
                {isLoading ? (
                    <div className="flex items-center justify-center gap-2 pt-24 text-sm text-[#74837d]">
                        <LoaderCircle className="size-4 animate-spin" />
                        会話履歴を読み込んでいます
                    </div>
                ) : loadError ? (
                    <div className="pt-24 text-center text-sm text-destructive">
                        会話履歴を取得できませんでした。
                    </div>
                ) : messages.length === 0 ? (
                    <section className="mx-auto flex max-w-2xl flex-col items-center pt-16 text-center sm:pt-24">
                        <div className="mb-5 flex size-12 items-center justify-center rounded-2xl bg-[#e8f0eb] text-[#245445]">
                            <Sparkles className="size-5" />
                        </div>
                        <h1 className="text-2xl font-semibold tracking-tight text-[#18352d] sm:text-3xl">
                            論文について、何でも聞いてください
                        </h1>
                        <p className="mt-3 max-w-lg text-sm leading-6 text-[#74837d]">
                            アップロードされた論文を横断検索し、根拠となる引用とともに回答します。
                        </p>
                        <div className="mt-8 grid w-full gap-2 sm:grid-cols-3">
                            {suggestions.map((suggestion) => (
                                <button
                                    type="button"
                                    key={suggestion}
                                    onClick={() =>
                                        onSuggestionSelect(suggestion)
                                    }
                                    className="rounded-xl border border-[#e1e7e3] bg-white p-4 text-left text-[12px] leading-5 text-[#52645d] transition-all hover:border-[#b9cbc2] hover:bg-[#f9fbf9] hover:text-[#24483b]"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </section>
                ) : (
                    <div className="space-y-8">
                        {messages.map((message) =>
                            message.role === "user" ? (
                                <section
                                    key={message.id}
                                    className="flex justify-end"
                                >
                                    <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-[#e9efeb] px-4 py-3 text-[13px] leading-6 text-[#30463e] sm:max-w-[75%]">
                                        {message.content}
                                        {message.status === "failed" && (
                                            <p className="mt-1 text-[10px] text-destructive">
                                                送信できませんでした
                                            </p>
                                        )}
                                    </div>
                                </section>
                            ) : (
                                <section
                                    key={message.id}
                                    className="flex gap-3 sm:gap-4"
                                >
                                    <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-xl bg-[#163d32] text-white shadow-sm">
                                        <Sparkles className="size-3.5" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="mb-3 text-[13px] font-semibold text-[#263f36]">
                                            PaperBuddy
                                        </p>
                                        <p className="whitespace-pre-wrap text-[13px] leading-7 text-[#43584f]">
                                            {message.content}
                                        </p>
                                    </div>
                                </section>
                            ),
                        )}
                        {isSending && (
                            <section className="flex gap-3 sm:gap-4">
                                <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-xl bg-[#163d32] text-white shadow-sm">
                                    <Sparkles className="size-3.5" />
                                </div>
                                <div className="flex items-center gap-2 py-2 text-xs text-[#74837d]">
                                    <LoaderCircle className="size-3.5 animate-spin" />
                                    回答を生成しています
                                </div>
                            </section>
                        )}
                    </div>
                )}
            </div>
        </ScrollArea>
    );
}
