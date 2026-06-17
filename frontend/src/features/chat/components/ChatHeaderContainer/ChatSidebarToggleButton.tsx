import { PanelLeftClose } from "lucide-react";
import { Button } from "@/components/shadcn/button";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/shadcn/tooltip";
import { cn } from "@/lib/utils";

type ChatSidebarToggleButtonProps = {
    sidebarOpen: boolean;
    onSidebarOpenChange: (open: boolean) => void;
};

export function ChatSidebarToggleButton({
    sidebarOpen,
    onSidebarOpenChange,
}: ChatSidebarToggleButtonProps) {
    return (
        <Tooltip>
            <TooltipTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="hidden text-[#65756f] lg:inline-flex"
                    onClick={() => onSidebarOpenChange(!sidebarOpen)}
                    aria-label="サイドバーを切り替える"
                >
                    <PanelLeftClose
                        className={cn(
                            "transition-transform",
                            !sidebarOpen && "rotate-180",
                        )}
                    />
                </Button>
            </TooltipTrigger>
            <TooltipContent>サイドバーを切り替える</TooltipContent>
        </Tooltip>
    );
}
