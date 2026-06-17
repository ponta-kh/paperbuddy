type AssistantAnswerContentProps = {
    content: string;
};

export function AssistantAnswerContent({
    content,
}: AssistantAnswerContentProps) {
    return (
        <p className="whitespace-pre-wrap text-[13px] leading-7 text-[#43584f]">
            {content}
        </p>
    );
}
