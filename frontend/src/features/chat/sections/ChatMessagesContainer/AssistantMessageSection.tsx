import { Sparkles } from "lucide-react";

import { AssistantAnswerContent } from "@/features/chat/components/ChatMessagesContainer/AssistantAnswerContent";
import { ChatCitationList } from "@/features/chat/components/ChatMessagesContainer/ChatCitationList";
import type { ChatMessage } from "@/lib/chat-api";

type AssistantMessageSectionProps = {
    message: ChatMessage;
};

export function AssistantMessageSection({
    message,
}: AssistantMessageSectionProps) {
    const citations =
        message.status === "revealing" ? [] : (message.citations ?? []);

    return (
        <section className="flex gap-3 sm:gap-4">
            <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-xl bg-[#163d32] text-white shadow-sm">
                <Sparkles className="size-3.5" />
            </div>
            <div className="min-w-0 flex-1">
                <p className="mb-3 text-[13px] font-semibold text-[#263f36]">
                    PaperBuddy
                </p>
                <AssistantAnswerContent content={message.content} />
                <ChatCitationList citations={citations} />
            </div>
        </section>
    );
}
