import { LogOut, MoreHorizontal } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/shadcn/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/shadcn/dropdown-menu";

export type ChatAccount = {
    displayName: string;
    initials: string;
};

type ChatAccountMenuProps = {
    account: ChatAccount;
    onSignOut: () => void;
};

export function ChatAccountMenu({ account, onSignOut }: ChatAccountMenuProps) {
    return (
        <div className="border-t border-[#dfe4df] p-3">
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <button
                        type="button"
                        className="flex w-full items-center gap-3 rounded-xl p-2 text-left transition-colors hover:bg-[#e9ece8]"
                        aria-label="アカウントメニュー"
                    >
                        <Avatar>
                            <AvatarFallback className="bg-[#dce8e1] text-xs font-semibold text-[#245445]">
                                {account.initials}
                            </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 flex-1">
                            <p className="truncate text-[13px] font-medium text-[#263b34]">
                                {account.displayName}
                            </p>
                        </div>
                        <MoreHorizontal className="size-4 text-[#7b8984]" />
                    </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-52">
                    <DropdownMenuItem onSelect={onSignOut}>
                        <LogOut />
                        ログアウト
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </div>
    );
}
