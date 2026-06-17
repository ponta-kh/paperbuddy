import { Badge } from "@/components/shadcn/badge";

type IndexedPaperCountProps = {
    count: number;
    isLoading: boolean;
    loadError: boolean;
};

export function IndexedPaperCount({
    count,
    isLoading,
    loadError,
}: IndexedPaperCountProps) {
    const label = isLoading
        ? "papers loading"
        : loadError
          ? "papers unavailable"
          : `${count} papers indexed`;

    return (
        <Badge
            variant="outline"
            className="hidden gap-1.5 rounded-full border-[#dbe5df] bg-[#f5f8f6] px-2.5 py-1 text-[10px] font-medium text-[#567268] sm:flex"
        >
            <span
                className={`size-1.5 rounded-full ${
                    loadError ? "bg-destructive" : "bg-[#5b9b78]"
                }`}
            />
            {label}
        </Badge>
    );
}
