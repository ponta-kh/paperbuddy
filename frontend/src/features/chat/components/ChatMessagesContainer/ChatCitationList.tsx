import { FileText } from "lucide-react";

import type { ChatCitation, ChatCitationSource } from "@/lib/chat-api";

type ChatCitationListProps = {
    citations: ChatCitation[];
};

export function ChatCitationList({ citations }: ChatCitationListProps) {
    if (citations.length === 0) return null;

    const sources = citations.flatMap((citation) =>
        citation.sources.map((source) => ({
            source,
            key: `${citation.text}-${source.uri ?? ""}-${source.content}`,
        })),
    );

    if (sources.length === 0) return null;

    return (
        <details className="group mt-4 rounded-lg border border-[#dfe7e2] bg-[#fbfcfa]">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-[12px] font-medium text-[#36564a] marker:hidden">
                <span>引用 {sources.length}件</span>
                <span className="text-[11px] text-[#6f8179] group-open:hidden">
                    表示
                </span>
                <span className="hidden text-[11px] text-[#6f8179] group-open:inline">
                    閉じる
                </span>
            </summary>
            <div className="border-t border-[#e5ebe7] px-3 py-3">
                <ol className="space-y-3">
                    {sources.map(({ source, key }, index) => (
                        <li key={key} className="min-w-0">
                            <div className="mb-1 flex min-w-0 items-center gap-2 text-[12px] font-medium text-[#2d4a40]">
                                <span className="flex size-5 shrink-0 items-center justify-center rounded-md bg-[#e6eee9] text-[#245445]">
                                    <FileText className="size-3" />
                                </span>
                                <span className="truncate">
                                    [{index + 1}] {sourceLabel(source)}
                                </span>
                            </div>
                            <p className="line-clamp-3 break-words pl-7 text-[12px] leading-5 text-[#60736b]">
                                {source.content}
                            </p>
                        </li>
                    ))}
                </ol>
            </div>
        </details>
    );
}

function sourceLabel(source: ChatCitationSource): string {
    const title = metadataText(source.metadata, "title");
    const fileName = metadataText(source.metadata, "file_name");
    const page = metadataText(source.metadata, "page");
    const name = title ?? fileName ?? fileNameFromUri(source.uri) ?? "参照元";

    return page ? `${name} / p.${page}` : name;
}

function metadataText(
    metadata: Record<string, unknown>,
    key: string,
): string | undefined {
    const value = metadata[key];
    if (typeof value === "string" && value.trim()) return value;
    if (typeof value === "number") return String(value);
    return undefined;
}

function fileNameFromUri(uri: string | null): string | undefined {
    if (!uri) return undefined;

    const path = uri.split(/[?#]/)[0] ?? uri;
    const fileName = path.split("/").filter(Boolean).at(-1);
    return fileName || undefined;
}
