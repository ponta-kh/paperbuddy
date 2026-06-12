import { useEffect, useState } from "react";

import { LibraryHeaderActionsView } from "@/features/chat/components/library/LibraryHeaderActionsView";
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
        <LibraryHeaderActionsView
            files={files}
            isLoading={isLoading}
            loadError={loadError}
            libraryOpen={libraryOpen}
            onLibraryOpenChange={setLibraryOpen}
        />
    );
}
