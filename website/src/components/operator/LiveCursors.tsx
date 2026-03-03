"use client";

import { useWindowSize } from "react-use";

interface Cursor {
    x: number;
    y: number;
    color: string;
}

interface LiveCursorsProps {
    cursors: Map<number, Cursor>;
}

export function LiveCursors({ cursors }: LiveCursorsProps) {
    const { width, height } = useWindowSize();

    return (
        <div className="pointer-events-none fixed inset-0 z-50 overflow-hidden">
            {Array.from(cursors.entries()).map(([clientId, cursor]) => {
                // Prevent rendering outside bounds if window sizes differ greatly
                if (cursor.x > width || cursor.y > height) return null;

                return (
                    <div
                        key={clientId}
                        className="absolute top-0 left-0 transition-all duration-100 ease-linear"
                        style={{
                            transform: `translate(${cursor.x}px, ${cursor.y}px)`,
                        }}
                    >
                        <svg
                            width="24"
                            height="36"
                            viewBox="0 0 24 36"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                            className="drop-shadow-md"
                        >
                            <path
                                d="M5.65376 21.1598L2.06603 3.65593C1.65991 1.67389 3.86877 0.176418 5.61747 1.24647L22.0465 11.2991C23.9463 12.4616 23.6308 15.3407 21.5367 16.0336L15.3942 18.0664C14.7354 18.2845 14.197 18.7844 13.9298 19.4267L11.5358 25.1834C10.7412 27.0941 7.84273 27.0515 7.11215 25.1157L5.65376 21.1598Z"
                                fill={cursor.color}
                                stroke="white"
                                strokeWidth="2"
                                strokeLinejoin="round"
                            />
                        </svg>
                        <div
                            className="absolute left-6 top-6 px-2 py-1 bg-zinc-900 border border-zinc-700 text-white text-[10px] font-medium rounded-md whitespace-nowrap shadow-lg"
                            style={{ backgroundColor: cursor.color }}
                        >
                            Operator {clientId.toString().slice(-4)}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
