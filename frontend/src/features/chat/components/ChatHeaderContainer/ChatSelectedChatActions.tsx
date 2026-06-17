import { Separator } from "@/components/shadcn/separator";
import { ChatActionsMenu } from "@/features/chat/components/ChatHeaderContainer/ChatActionsMenu";

type ChatSelectedChatActionsProps = {
    title: string;
    onDeleteChat: () => Promise<void>;
    onRenameChat: (title: string) => Promise<void>;
};

export function ChatSelectedChatActions({
    title,
    onDeleteChat,
    onRenameChat,
}: ChatSelectedChatActionsProps) {
    return (
        <>
            <Separator orientation="vertical" className="mx-1 h-5" />

            <ChatActionsMenu
                title={title}
                onDelete={onDeleteChat}
                onRename={onRenameChat}
            />
        </>
    );
}
