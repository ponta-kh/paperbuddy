import { useEffect, useState } from "react";

import { ChatComposer } from "@/components/chat/ChatComposer";
import { ChatConversation } from "@/components/chat/ChatConversation";
import { ChatHeader } from "@/components/chat/ChatHeader";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { TooltipProvider } from "@/components/shadcn/tooltip";
import {
    type ChatMessage,
    type ChatSummary,
    deleteChat,
    getChatMessages,
    getChats,
    renameChat,
    sendPrompt,
} from "@/lib/chat-api";
import { cn } from "@/lib/utils";

function Chat() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [message, setMessage] = useState("");
    const [chats, setChats] = useState<ChatSummary[]>([]);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [selectedChatId, setSelectedChatId] = useState<string>();
    const [isChatsLoading, setIsChatsLoading] = useState(true);
    const [isMessagesLoading, setIsMessagesLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [chatsError, setChatsError] = useState(false);
    const [messagesError, setMessagesError] = useState(false);
    const [sendError, setSendError] = useState(false);

    const selectedChat = chats.find((chat) => chat.id === selectedChatId);

    useEffect(() => {
        const controller = new AbortController();

        getChats(controller.signal)
            .then((response) => {
                setChats(response);
                setChatsError(false);
            })
            .catch((error: unknown) => {
                if (
                    error instanceof DOMException &&
                    error.name === "AbortError"
                )
                    return;
                setChatsError(true);
            })
            .finally(() => {
                if (!controller.signal.aborted) setIsChatsLoading(false);
            });

        return () => controller.abort();
    }, []);

    useEffect(() => {
        if (!selectedChatId) {
            setMessages([]);
            setMessagesError(false);
            return;
        }

        const controller = new AbortController();
        setIsMessagesLoading(true);

        getChatMessages(selectedChatId, controller.signal)
            .then((response) => {
                setMessages(response);
                setMessagesError(false);
            })
            .catch((error: unknown) => {
                if (
                    error instanceof DOMException &&
                    error.name === "AbortError"
                )
                    return;
                setMessagesError(true);
            })
            .finally(() => {
                if (!controller.signal.aborted) setIsMessagesLoading(false);
            });

        return () => controller.abort();
    }, [selectedChatId]);

    const handleSubmit = async () => {
        const trimmedMessage = message.trim();
        if (!trimmedMessage || isSending) return;

        const optimisticMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: trimmedMessage,
            createdAt: new Date().toISOString(),
        };

        setMessages((currentMessages) => [
            ...currentMessages,
            optimisticMessage,
        ]);
        setIsSending(true);
        setSendError(false);

        try {
            const chatId = await sendPrompt(trimmedMessage, selectedChatId);
            const [updatedChats, updatedMessages] = await Promise.all([
                getChats(),
                getChatMessages(chatId),
            ]);

            setSelectedChatId(chatId);
            setChats(updatedChats);
            setMessages(updatedMessages);
            setChatsError(false);
            setMessagesError(false);
            setMessage("");
        } catch {
            setMessages((currentMessages) =>
                currentMessages.filter(
                    (currentMessage) =>
                        currentMessage.id !== optimisticMessage.id,
                ),
            );
            setSendError(true);
        } finally {
            setIsSending(false);
        }
    };

    const handleNewChat = () => {
        setSelectedChatId(undefined);
        setMessages([]);
        setMessage("");
        setSendError(false);
    };

    const handleChatSelect = (chatId: string) => {
        setSelectedChatId(chatId);
        setMobileMenuOpen(false);
        setSendError(false);
    };

    const handleRenameChat = async (title: string) => {
        if (!selectedChatId) return;

        await renameChat(selectedChatId, title);
        setChats((currentChats) =>
            currentChats.map((chat) =>
                chat.id === selectedChatId ? { ...chat, title } : chat,
            ),
        );
    };

    const handleDeleteChat = async () => {
        if (!selectedChatId) return;

        await deleteChat(selectedChatId);
        setChats((currentChats) =>
            currentChats.filter((chat) => chat.id !== selectedChatId),
        );
        handleNewChat();
    };

    return (
        <TooltipProvider>
            <div className="flex h-dvh overflow-hidden bg-[#fbfcfa] text-[#263b34]">
                <aside
                    className={cn(
                        "hidden shrink-0 overflow-hidden border-r border-[#e1e6e2] transition-[width] duration-300 lg:block",
                        sidebarOpen ? "w-64" : "w-0 border-r-0",
                    )}
                >
                    <div className="h-full w-64">
                        <ChatSidebar
                            chats={chats}
                            chatsError={chatsError}
                            isLoading={isChatsLoading}
                            selectedChatId={selectedChatId}
                            onChatSelect={handleChatSelect}
                            onNewChat={handleNewChat}
                        />
                    </div>
                </aside>

                <main className="relative flex min-w-0 flex-1 flex-col">
                    <ChatHeader
                        chats={chats}
                        chatsError={chatsError}
                        isChatsLoading={isChatsLoading}
                        mobileMenuOpen={mobileMenuOpen}
                        selectedChatId={selectedChatId}
                        sidebarOpen={sidebarOpen}
                        title={selectedChat?.title}
                        onChatSelect={handleChatSelect}
                        onDeleteChat={handleDeleteChat}
                        onMobileMenuOpenChange={setMobileMenuOpen}
                        onNewChat={handleNewChat}
                        onRenameChat={handleRenameChat}
                        onSidebarOpenChange={setSidebarOpen}
                    />
                    <ChatConversation
                        isLoading={isMessagesLoading}
                        isSending={isSending}
                        loadError={messagesError}
                        messages={messages}
                        onSuggestionSelect={setMessage}
                    />
                    <ChatComposer
                        isSending={isSending}
                        message={message}
                        sendError={sendError}
                        onMessageChange={setMessage}
                        onSubmit={handleSubmit}
                    />
                </main>
            </div>
        </TooltipProvider>
    );
}

export default Chat;
