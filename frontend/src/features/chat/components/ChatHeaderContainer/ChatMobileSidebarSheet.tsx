import { Menu } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/shadcn/button";
import {
    Sheet,
    SheetContent,
    SheetTitle,
    SheetTrigger,
} from "@/components/shadcn/sheet";

type ChatMobileSidebarSheetProps = {
    children: ReactNode;
    open: boolean;
    onOpenChange: (open: boolean) => void;
};

export function ChatMobileSidebarSheet({
    children,
    open,
    onOpenChange,
}: ChatMobileSidebarSheetProps) {
    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="lg:hidden"
                    aria-label="メニューを開く"
                >
                    <Menu />
                </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-72 p-0">
                <SheetTitle className="sr-only">チャットメニュー</SheetTitle>
                {children}
            </SheetContent>
        </Sheet>
    );
}
