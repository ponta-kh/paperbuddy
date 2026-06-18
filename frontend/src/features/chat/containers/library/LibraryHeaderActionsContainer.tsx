import { useEffect, useState } from "react";

import { LibraryHeaderActions } from "@/features/chat/components/LibraryHeaderActionsContainer/LibraryHeaderActions";
import { getIndexedFiles, type IndexedFile } from "@/lib/library-api";

export function LibraryHeaderActionsContainer() {
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
        <LibraryHeaderActions
            files={files}
            isLoading={isLoading}
            loadError={loadError}
            libraryOpen={libraryOpen}
            onLibraryOpenChange={setLibraryOpen}
        />
    );
}
