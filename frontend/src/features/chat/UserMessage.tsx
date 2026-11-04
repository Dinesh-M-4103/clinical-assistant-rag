export function UserMessage({ content }: { content: string }) {
  return (
    <article aria-label="Your question" className="flex justify-end">
      <p className="max-w-[88%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-[15px] leading-relaxed text-primary-foreground shadow-soft md:max-w-[80%]">
        {content}
      </p>
    </article>
  );
}
