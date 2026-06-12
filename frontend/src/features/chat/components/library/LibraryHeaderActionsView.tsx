import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/shadcn/sheet";
import { IndexedPaperCount } from "@/features/chat/components/library/IndexedPaperCount";
import { LibraryButton } from "@/features/chat/components/library/LibraryButton";
import { LibraryFileList } from "@/features/chat/components/library/LibraryFileList";
import type { IndexedFile } from "@/lib/library-api";

type LibraryHeaderActionsViewProps = {
    files: IndexedFile[];
    isLoading: boolean;
    loadError: boolean;
    libraryOpen: boolean;
    onLibraryOpenChange: (open: boolean) => void;
};

export function LibraryHeaderActionsView({
    files,
    isLoading,
    loadError,
    libraryOpen,
    onLibraryOpenChange,
}: LibraryHeaderActionsViewProps) {
    return (
        <>
            <div className="flex items-center gap-2">
                <IndexedPaperCount
                    count={files.length}
                    isLoading={isLoading}
                    loadError={loadError}
                />
                <LibraryButton onClick={() => onLibraryOpenChange(true)} />
            </div>
            <Sheet open={libraryOpen} onOpenChange={onLibraryOpenChange}>
                <SheetContent className="w-full sm:max-w-md">
                    <SheetHeader>
                        <SheetTitle>ライブラリ</SheetTitle>
                        <SheetDescription>
                            RAGへ取り込み済みのデータソース一覧
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
