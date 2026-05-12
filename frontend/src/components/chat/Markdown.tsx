"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function Markdown({ children }: { children: string }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="md-p">{children}</p>,
          h1: ({ children }) => <h1 className="md-h md-h1">{children}</h1>,
          h2: ({ children }) => <h2 className="md-h md-h2">{children}</h2>,
          h3: ({ children }) => <h3 className="md-h md-h3">{children}</h3>,
          h4: ({ children }) => <h4 className="md-h md-h4">{children}</h4>,
          ul: ({ children }) => <ul className="md-ul">{children}</ul>,
          ol: ({ children }) => <ol className="md-ol">{children}</ol>,
          li: ({ children }) => <li className="md-li">{children}</li>,
          a: ({ href, children }) => (
            <a className="md-a" href={href} target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
          strong: ({ children }) => <strong className="md-strong">{children}</strong>,
          em: ({ children }) => <em className="md-em">{children}</em>,
          blockquote: ({ children }) => <blockquote className="md-quote">{children}</blockquote>,
          hr: () => <hr className="md-hr" />,
          code: ({ className, children, ...props }) => {
            const inline = !/language-/.test(className ?? "");
            if (inline) {
              return (
                <code className="md-code-inline" {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={`md-code-block ${className ?? ""}`} {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => <pre className="md-pre">{children}</pre>,
          table: ({ children }) => (
            <div className="md-table-wrap">
              <table className="md-table">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="md-thead">{children}</thead>,
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => <tr className="md-tr">{children}</tr>,
          th: ({ children, style }) => (
            <th className="md-th" style={style}>
              {children}
            </th>
          ),
          td: ({ children, style }) => (
            <td className="md-td" style={style}>
              {children}
            </td>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
