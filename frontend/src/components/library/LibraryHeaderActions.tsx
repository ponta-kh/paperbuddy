import { useEffect, useState } from "react";

import { IndexedPaperCount } from "@/components/library/IndexedPaperCount";
import { LibraryButton } from "@/components/library/LibraryButton";
import { LibraryFileList } from "@/components/library/LibraryFileList";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/shadcn/sheet";
import { getIndexedFiles, type IndexedFile } from "@/lib/library-api";

export function LibraryHeaderActions() {
    const [files, setFiles] = useState<IndexedFile[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [loadError, setLoadError] = useState(false);
    const [libraryOpen, setLibraryOpen] = useState(false);

    useEffect(() => {
        const controller = new AbortController();

        getIndexedFiles(controller.signal)
            .then((response) => {
                setFiles(response);
                setLoadError(false);
            })
            .catch((error: unknown) => {
                if (
                    error instanceof DOMException &&
                    error.name === "AbortError"
                )
                    return;
                setLoadError(true);
            })
            .finally(() => {
                if (!controller.signal.aborted) setIsLoading(false);
            });

        return () => controller.abort();
    }, []);

    return (
        <>
            <div className="flex items-center gap-2">
                <IndexedPaperCount
                    count={files.length}
                    isLoading={isLoading}
                    loadError={loadError}
                />
                <LibraryButton onClick={() => setLibraryOpen(true)} />
            </div>
            <Sheet open={libraryOpen} onOpenChange={setLibraryOpen}>
                <SheetContent className="w-full sm:max-w-md">
                    <SheetHeader>
                        <SheetTitle>ライブラリ</SheetTitle>
                        <SheetDescription>
                            RAGへ取り込み済みのファイル一覧
                        </SheetDescription>
                    </SheetHeader>
                    <LibraryFileList
                        files={files}
                        isLoading={isLoading}
                        loadError={loadError}
                    />
                </SheetContent>
            </Sheet>
        </>
    );
}
