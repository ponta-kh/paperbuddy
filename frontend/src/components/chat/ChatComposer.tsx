import { ArrowUp } from 'lucide-react'

import { Button } from '@/components/shadcn/button'
import { Textarea } from '@/components/shadcn/textarea'

type ChatComposerProps = {
  isSending: boolean
  message: string
  sendError: boolean
  onMessageChange: (message: string) => void
  onSubmit: () => void
}

export function ChatComposer({
  isSending,
  message,
  sendError,
  onMessageChange,
  onSubmit,
}: ChatComposerProps) {
  return (
    <footer className="relative z-10 shrink-0 bg-[#fbfcfa] px-3 pb-3 pt-2 sm:px-6 sm:pb-4">
      <div className="pointer-events-none absolute inset-x-0 bottom-full h-12 bg-gradient-to-t from-[#fbfcfa] to-transparent" />
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-[26px] border border-[#dbe3de] bg-white p-2 shadow-[0_8px_28px_-14px_rgba(35,64,52,0.4)]">
          <Textarea
            value={message}
            onChange={(event) => onMessageChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                onSubmit()
              }
            }}
            placeholder="論文について質問する..."
            disabled={isSending}
            className="max-h-40 min-h-10 flex-1 resize-none border-0 bg-transparent px-3 py-2 text-[14px] shadow-none focus-visible:ring-0"
          />
          <Button
            size="icon"
            className="mb-0.5 shrink-0 rounded-full bg-[#163d32] text-white hover:bg-[#285446]"
            disabled={!message.trim() || isSending}
            onClick={onSubmit}
            aria-label={isSending ? '送信中' : '送信'}
          >
            <ArrowUp className={isSending ? 'animate-pulse' : undefined} />
          </Button>
        </div>
        {sendError && (
          <p className="mt-2 px-2 text-center text-[10px] text-destructive">
            メッセージを送信できませんでした。もう一度お試しください。
          </p>
        )}
        <div className="mt-2 flex flex-col items-center justify-between gap-1 px-2 text-[9px] text-[#9ba6a1] sm:flex-row">
          <span>Shift + Enterで改行</span>
          <span>
            回答は不正確な場合があります。重要な情報は参照論文を確認してください。
          </span>
        </div>
      </div>
    </footer>
  )
}
