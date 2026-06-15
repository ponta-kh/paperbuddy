import { requestJson } from "@/lib/api-client";

export type ChatSummary = {
    id: string;
    title: string;
    updatedAt: string;
};

export type ChatMessage = {
    id: string;
    role: "user" | "assistant";
    content: string;
    createdAt: string;
};

type ChatSummaryResponse = {
    chat_id: string;
    title: string;
    created_at: string;
    last_updated_at: string;
};

type ChatMessageResponse = {
    turn_id: string;
    sender: "user" | "llm";
    content: string;
    sent_at: string;
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
            id: `${message.turn_id}:${message.sender}`,
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
): Promise<ChatSummary> {
    const path = chatId
        ? `/chats/${encodeURIComponent(chatId)}/messages`
        : "/chats";
    const response = await requestJson<SendPromptResponse>(path, {
        method: "POST",
        body: { prompt },
    });

    return {
        id: response.chat_id,
        title: response.title,
        updatedAt: response.last_updated_at,
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
