import { BookOpen } from "lucide-react";

export function ChatSidebarBrand() {
    return (
        <div className="flex h-16 items-center gap-2 px-4">
            <div className="flex size-8 items-center justify-center rounded-xl bg-[#163d32] text-white shadow-sm">
                <BookOpen className="size-4" strokeWidth={2.25} />
            </div>
            <span className="text-[17px] font-semibold tracking-tight text-[#18352d]">
                PaperBuddy
            </span>
        </div>
    );
}
