import { Plus } from "lucide-react";
import { Button } from "@/components/shadcn/button";

type ChatNewChatButtonProps = {
    onNewChat: () => void;
};

export function ChatNewChatButton({ onNewChat }: ChatNewChatButtonProps) {
    return (
        <div className="px-3 pb-3">
            <Button
                className="h-10 w-full justify-start gap-2.5 rounded-xl bg-[#163d32] px-3 text-white shadow-sm hover:bg-[#214e41]"
                onClick={onNewChat}
            >
                <Plus className="size-4" />
                新しいチャット
            </Button>
        </div>
    );
}
