import { RefreshCw, ShieldAlert } from "lucide-react";

import { Button } from "@/components/shadcn/button";

type SystemErrorScreenProps = {
    onReload?: () => void;
};

export function SystemErrorScreen({
    onReload = () => window.location.reload(),
}: SystemErrorScreenProps) {
    return (
        <main className="relative flex min-h-dvh items-center justify-center overflow-hidden bg-[#f5f8f6] px-5 py-12 text-[#263b34]">
            <div
                aria-hidden="true"
                className="absolute inset-x-0 top-0 h-64 bg-[radial-gradient(circle_at_top,#dcebe3_0%,transparent_68%)]"
            />
            <section className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-[#dce5e0] bg-white shadow-[0_24px_70px_-36px_rgba(22,61,50,0.38)]">
                <div className="h-1.5 bg-[#c97961]" />
                <div className="px-6 py-8 sm:px-10 sm:py-10">
                    <div className="flex size-14 items-center justify-center rounded-2xl bg-[#f8e9e4] text-[#a54832]">
                        <ShieldAlert className="size-6" aria-hidden="true" />
                    </div>

                    <p className="mt-7 text-xs font-semibold tracking-[0.16em] text-[#9a5a48] uppercase">
                        System Error
                    </p>
                    <h1 className="mt-2 text-2xl font-semibold tracking-tight text-[#18352d] sm:text-3xl">
                        システム側で不具合が発生しています
                    </h1>
                    <p className="mt-4 text-sm leading-7 text-[#64766f]">
                        認証サービスの設定を読み込めないため、PaperBuddyを開始できませんでした。
                        お客様の操作やアカウントに問題がある状態ではありません。
                    </p>

                    <div className="mt-7 rounded-2xl border border-[#e3e9e5] bg-[#f8faf9] px-5 py-4">
                        <p className="text-sm font-medium text-[#334a42]">
                            お手数ですが、時間を置いてから再読み込みしてください。
                        </p>
                        <p className="mt-1.5 text-xs leading-5 text-[#74837d]">
                            再読み込み後も解消しない場合は、管理者へお問い合わせください。
                        </p>
                    </div>

                    <Button
                        type="button"
                        size="lg"
                        onClick={onReload}
                        className="mt-7 h-11 bg-[#163d32] px-5 text-white hover:bg-[#245445]"
                    >
                        <RefreshCw aria-hidden="true" />
                        再読み込みする
                    </Button>
                </div>
            </section>
        </main>
    );
}
