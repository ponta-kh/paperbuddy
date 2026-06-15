import { useState } from "react";

import { TooltipProvider } from "@/components/shadcn/tooltip";
import { ChatComposer } from "@/features/chat/components/ChatComposer";
import { ChatConversation } from "@/features/chat/components/ChatConversation";
import { ChatHeader } from "@/features/chat/components/ChatHeader";
import { ChatSidebar } from "@/features/chat/components/ChatSidebar";
import { ChatMessagesContainer } from "@/features/chat/containers/ChatMessagesContainer";
import { ChatThreadsContainer } from "@/features/chat/containers/ChatThreadsContainer";
import { LibraryHeaderActionsContainer } from "@/features/chat/containers/library/LibraryHeaderActionsContainer";
import { type ChatSummary, sendPrompt } from "@/lib/chat-api";

function ChatPage() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [message, setMessage] = useState("");
    const [selectedChatId, setSelectedChatId] = useState<string>();
    const [isSending, setIsSending] = useState(false);
    const [sendError, setSendError] = useState(false);
    const [messageResetKey, setMessageResetKey] = useState(0);

    const handleSubmit = async (
        isContinuationExpired: boolean,
        onUpsertChat: (chat: ChatSummary) => void,
        onAppendUserMessage: (content: string) => string,
        onAppendAssistantMessage: (content: string) => void,
        onBindCurrentChat: (chatId: string) => void,
        onMarkMessageCompleted: (messageId: string) => void,
        onMarkMessageFailed: (messageId: string) => void,
    ) => {
        const trimmedMessage = message.trim();
        if (!trimmedMessage || isSending || isContinuationExpired) return;

        const userMessageId = onAppendUserMessage(trimmedMessage);
        setMessage("");
        setIsSending(true);
        setSendError(false);

        try {
            const { chat, answer } = await sendPrompt(
                trimmedMessage,
                selectedChatId,
            );
            onBindCurrentChat(chat.id);
            setSelectedChatId(chat.id);
            onMarkMessageCompleted(userMessageId);
            onAppendAssistantMessage(answer);
            onUpsertChat(chat);
        } catch {
            onMarkMessageFailed(userMessageId);
            setSendError(true);
        } finally {
            setIsSending(false);
        }
    };

    const handleNewChat = () => {
        setSelectedChatId(undefined);
        setMessage("");
        setSendError(false);
        setMessageResetKey((current) => current + 1);
    };

    const handleChatSelect = (chatId: string) => {
        setSelectedChatId(chatId);
        setMobileMenuOpen(false);
        setSendError(false);
    };

    return (
        <TooltipProvider>
            <div className="flex h-dvh overflow-hidden bg-[#fbfcfa] text-[#263b34]">
                <ChatThreadsContainer selectedChatId={selectedChatId}>
                    {({
                        chats,
                        chatsError,
                        isLoading,
                        isContinuationExpired,
                        title,
                        onDeleteChat,
                        onRenameChat,
                        onUpsertChat,
                    }) => (
                        <>
                            <aside
                                className={
                                    sidebarOpen
                                        ? "hidden shrink-0 overflow-hidden border-r border-[#e1e6e2] transition-[width] duration-300 lg:block lg:w-64"
                                        : "hidden shrink-0 overflow-hidden border-r-0 transition-[width] duration-300 lg:block lg:w-0"
                                }
                            >
                                <div className="h-full w-64">
                                    <ChatSidebar
                                        chats={chats}
                                        chatsError={chatsError}
                                        isLoading={isLoading}
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
                                    headerActions={
                                        <LibraryHeaderActionsContainer />
                                    }
                                    isChatsLoading={isLoading}
                                    mobileMenuOpen={mobileMenuOpen}
                                    selectedChatId={selectedChatId}
                                    sidebarOpen={sidebarOpen}
                                    title={title}
                                    onChatSelect={handleChatSelect}
                                    onDeleteChat={async () => {
                                        await onDeleteChat();
                                        handleNewChat();
                                    }}
                                    onMobileMenuOpenChange={setMobileMenuOpen}
                                    onNewChat={handleNewChat}
                                    onRenameChat={onRenameChat}
                                    onSidebarOpenChange={setSidebarOpen}
                                />
                                <ChatMessagesContainer
                                    key={messageResetKey}
                                    selectedChatId={selectedChatId}
                                >
                                    {({
                                        messages,
                                        isLoading: isMessagesLoading,
                                        loadError: messagesError,
                                        onAppendUserMessage,
                                        onAppendAssistantMessage,
                                        onBindCurrentChat,
                                        onMarkMessageCompleted,
                                        onMarkMessageFailed,
                                    }) => (
                                        <>
                                            <ChatConversation
                                                isLoading={isMessagesLoading}
                                                isSending={isSending}
                                                loadError={messagesError}
                                                messages={messages}
                                                onSuggestionSelect={setMessage}
                                            />
                                            <ChatComposer
                                                isContinuationExpired={
                                                    isContinuationExpired
                                                }
                                                isSending={isSending}
                                                message={message}
                                                sendError={sendError}
                                                onMessageChange={setMessage}
                                                onSubmit={() =>
                                                    handleSubmit(
                                                        isContinuationExpired,
                                                        onUpsertChat,
                                                        onAppendUserMessage,
                                                        onAppendAssistantMessage,
                                                        onBindCurrentChat,
                                                        onMarkMessageCompleted,
                                                        onMarkMessageFailed,
                                                    )
                                                }
                                            />
                                        </>
                                    )}
                                </ChatMessagesContainer>
                            </main>
                        </>
                    )}
                </ChatThreadsContainer>
            </div>
        </TooltipProvider>
    );
}

export default ChatPage;
