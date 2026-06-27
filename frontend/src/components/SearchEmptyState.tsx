import { SearchX } from "lucide-react";

import { cn } from "@/lib/utils";

type SearchEmptyStateProps = {
    message: string;
    className?: string;
};

export function SearchEmptyState({
    message,
    className,
}: SearchEmptyStateProps) {
    return (
        <div
            className={cn("flex items-start gap-2.5 text-[#74837d]", className)}
        >
            <SearchX className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <p className="leading-5">{message}</p>
        </div>
    );
}
