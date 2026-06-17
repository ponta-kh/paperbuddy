import { requestJson } from "@/lib/api-client";

export type ChatSummary = {
    id: string;
    title: string;
    updatedAt: string;
};

export type ChatCitationSource = {
    content: string;
    locationType: string | null;
    uri: string | null;
    metadata: Record<string, unknown>;
};

export type ChatCitation = {
    text: string;
    spanStart: number | null;
    spanEnd: number | null;
    sources: ChatCitationSource[];
};

export type ChatMessage = {
    id: string;
    role: "user" | "assistant";
    content: string;
    createdAt: string;
    citations?: ChatCitation[];
    status?: "pending" | "revealing" | "completed" | "failed";
};

export type SendPromptResult = {
    chat: ChatSummary;
    answer: string;
    citations: ChatCitation[];
};

type ChatSummaryResponse = {
    chat_id: string;
    title: string;
    created_at: string;
    last_updated_at: string;
};

type ChatMessageResponse = {
    request_id: string;
    sender: "user" | "llm";
    content: string;
    sent_at: string;
};

type ChatCitationSourceResponse = {
    content: string;
    location_type: string | null;
    uri: string | null;
    metadata: Record<string, unknown>;
};

type ChatCitationResponse = {
    text: string;
    span_start: number | null;
    span_end: number | null;
    sources: ChatCitationSourceResponse[];
};

type ListChatsResponse = {
    chats: ChatSummaryResponse[];
};

type ListChatMessagesResponse = {
    chat_id: string;
    messages: ChatMessageResponse[];
};

type SendPromptResponse = {
    chat_id: string;
    answer: string;
    citations?: ChatCitationResponse[];
    title: string;
    last_updated_at: string;
};

type RenameChatResponse = {
    chat_id: string;
    title: string;
};

export async function getChats(signal?: AbortSignal): Promise<ChatSummary[]> {
    const response = await requestJson<ListChatsResponse>("/chats", {
        method: "GET",
        signal,
    });

    return response.chats
        .map((chat) => ({
            id: chat.chat_id,
            title: chat.title,
            updatedAt: chat.last_updated_at,
        }))
        .sort(
            (first, second) =>
                new Date(second.updatedAt).getTime() -
                new Date(first.updatedAt).getTime(),
        );
}

export async function getChatMessages(
    chatId: string,
    signal?: AbortSignal,
): Promise<ChatMessage[]> {
    const chat = await requestJson<ListChatMessagesResponse>(
        `/chats/${encodeURIComponent(chatId)}/messages`,
        {
            method: "GET",
            signal,
        },
    );

    return chat.messages
        .map<ChatMessage>((message) => ({
            id: `${message.request_id}:${message.sender}`,
            role: message.sender === "user" ? "user" : "assistant",
            content: message.content,
            createdAt: message.sent_at,
        }))
        .sort(
            (first, second) =>
                new Date(first.createdAt).getTime() -
                new Date(second.createdAt).getTime(),
        );
}

export async function sendPrompt(
    prompt: string,
    chatId?: string,
): Promise<SendPromptResult> {
    const path = chatId
        ? `/chats/${encodeURIComponent(chatId)}/messages`
        : "/chats";
    const response = await requestJson<SendPromptResponse>(path, {
        method: "POST",
        body: { prompt },
    });

    return {
        chat: {
            id: response.chat_id,
            title: response.title,
            updatedAt: response.last_updated_at,
        },
        answer: response.answer,
        citations: (response.citations ?? []).map(toChatCitation),
    };
}

function toChatCitation(citation: ChatCitationResponse): ChatCitation {
    return {
        text: citation.text,
        spanStart: citation.span_start,
        spanEnd: citation.span_end,
        sources: citation.sources.map((source) => ({
            content: source.content,
            locationType: source.location_type,
            uri: source.uri,
            metadata: source.metadata,
        })),
    };
}

export async function renameChat(chatId: string, title: string): Promise<void> {
    await requestJson<RenameChatResponse>(
        `/chats/${encodeURIComponent(chatId)}`,
        {
            method: "PATCH",
            body: { title },
        },
    );
}

export async function deleteChat(chatId: string): Promise<void> {
    await requestJson<void>(`/chats/${encodeURIComponent(chatId)}`, {
        method: "DELETE",
    });
}
