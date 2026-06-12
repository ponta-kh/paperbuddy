import { Library } from "lucide-react";

import { Button } from "@/components/shadcn/button";

type LibraryButtonProps = {
    onClick: () => void;
};

export function LibraryButton({ onClick }: LibraryButtonProps) {
    return (
        <Button
            variant="outline"
            className="hidden rounded-lg border-[#dfe5e1] text-[12px] text-[#4b6259] sm:inline-flex"
            onClick={onClick}
        >
            <Library />
            ライブラリ
        </Button>
    );
}
