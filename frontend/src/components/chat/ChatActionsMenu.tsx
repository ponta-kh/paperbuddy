import { ChevronDown } from "lucide-react";
import { useState } from "react";

import {
    AlertDialog,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/shadcn/alert-dialog";
import { Button } from "@/components/shadcn/button";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/shadcn/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/shadcn/dropdown-menu";
import { Input } from "@/components/shadcn/input";

type ChatActionsMenuProps = {
    title: string;
    onDelete: () => Promise<void>;
    onRename: (title: string) => Promise<void>;
};

export function ChatActionsMenu({
    title,
    onDelete,
    onRename,
}: ChatActionsMenuProps) {
    const [renameOpen, setRenameOpen] = useState(false);
    const [deleteOpen, setDeleteOpen] = useState(false);
    const [newTitle, setNewTitle] = useState(title);
    const [isRenaming, setIsRenaming] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [renameError, setRenameError] = useState(false);
    const [deleteError, setDeleteError] = useState(false);

    const openRenameDialog = () => {
        setNewTitle(title);
        setRenameError(false);
        setRenameOpen(true);
    };

    const handleRenameOpenChange = (open: boolean) => {
        if (isRenaming) return;
        setRenameOpen(open);
    };

    const openDeleteDialog = () => {
        setDeleteError(false);
        setDeleteOpen(true);
    };

    const handleDeleteOpenChange = (open: boolean) => {
        if (isDeleting) return;
        setDeleteOpen(open);
    };

    const handleRename = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const trimmedTitle = newTitle.trim();
        if (!trimmedTitle || isRenaming) return;

        setIsRenaming(true);
        setRenameError(false);
        try {
            await onRename(trimmedTitle);
            setRenameOpen(false);
        } catch {
            setRenameError(true);
        } finally {
            setIsRenaming(false);
        }
    };

    const handleDelete = async () => {
        if (isDeleting) return;

        setIsDeleting(true);
        setDeleteError(false);
        try {
            await onDelete();
            setDeleteOpen(false);
        } catch {
            setDeleteError(true);
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="ghost"
                        className="gap-2 rounded-lg px-2 text-[13px] font-medium text-[#344a42]"
                    >
                        <span className="max-w-44 truncate sm:max-w-none">
                            {title}
                        </span>
                        <ChevronDown className="size-3.5 text-[#809089]" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-52">
                    <DropdownMenuItem onSelect={openRenameDialog}>
                        タイトルを変更
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                        variant="destructive"
                        onSelect={openDeleteDialog}
                    >
                        チャットを削除
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <Dialog open={renameOpen} onOpenChange={handleRenameOpenChange}>
                <DialogContent>
                    <form onSubmit={handleRename}>
                        <DialogHeader>
                            <DialogTitle>タイトルを変更</DialogTitle>
                            <DialogDescription>
                                チャットの新しいタイトルを入力してください。
                            </DialogDescription>
                        </DialogHeader>
                        <Input
                            className="my-4"
                            value={newTitle}
                            onChange={(event) =>
                                setNewTitle(event.target.value)
                            }
                            aria-label="新しいタイトル"
                            autoFocus
                            disabled={isRenaming}
                        />
                        {renameError && (
                            <p className="mb-4 text-sm text-destructive">
                                タイトルを変更できませんでした。
                            </p>
                        )}
                        <DialogFooter>
                            <DialogClose asChild>
                                <Button
                                    type="button"
                                    variant="outline"
                                    disabled={isRenaming}
                                >
                                    キャンセル
                                </Button>
                            </DialogClose>
                            <Button
                                type="submit"
                                disabled={!newTitle.trim() || isRenaming}
                            >
                                {isRenaming ? "更新中" : "更新"}
                            </Button>
                        </DialogFooter>
                    </form>
                </DialogContent>
            </Dialog>

            <AlertDialog
                open={deleteOpen}
                onOpenChange={handleDeleteOpenChange}
            >
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>チャットを削除</AlertDialogTitle>
                        <AlertDialogDescription>
                            「{title}」を削除します。<br />
                            この操作は取り消せません。
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    {deleteError && (
                        <p className="text-sm text-destructive">
                            チャットを削除できませんでした。
                        </p>
                    )}
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isDeleting}>
                            キャンセル
                        </AlertDialogCancel>
                        <Button
                            variant="destructive"
                            onClick={handleDelete}
                            disabled={isDeleting}
                        >
                            {isDeleting ? "削除中" : "削除"}
                        </Button>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </>
    );
}
