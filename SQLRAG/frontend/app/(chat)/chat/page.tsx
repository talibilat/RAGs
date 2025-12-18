"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getSession, clearSession } from "@/app/services/auth";
import { sendMessage, resumeChat, ChatResponse, User } from "@/app/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
    role: "user" | "assistant";
    content: string;
}

export default function ChatPage() {
    const router = useRouter();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [threadId] = useState(() => "thread_" + Math.random().toString(36).substr(2, 9));
    const [approvalParams, setApprovalParams] = useState<{ interruptId: string, summary: string, approvalToken: string } | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [role, setRole] = useState<string>("member");
    const [token, setToken] = useState<string | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    useEffect(() => {
        const session = getSession();
        if (!session) {
            router.push("/login");
        } else {
            setUser(session.user);
            setToken(session.token);
            setRole(session.user.role || "member");
        }
    }, [router]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg = input;
        setInput("");
        setMessages(prev => [...prev, { role: "user", content: userMsg }]);
        setLoading(true);

        try {
            if (!token) {
                router.push("/login");
                return;
            }
            const res = await sendMessage(threadId, userMsg, token);
            handleResponse(res);
        } catch (err) {
            toast.error("Failed to send message");
        } finally {
            setLoading(false);
        }
    };

    const handleResponse = (res: ChatResponse) => {
        if (res.type === "message") {
            if (res.content) {
                setMessages(prev => [...prev, { role: "assistant", content: res.content! }]);
            }
        } else if (res.type === "approval_required") {
            const planText = res.message || res.content || "Approval Required";
            setMessages(prev => [...prev, { role: "assistant", content: planText }]);
            setApprovalParams({ interruptId: res.interrupt_id!, summary: planText, approvalToken: res.approval_token! });
        }
    };

    const handleResume = async (approved: boolean) => {
        if (!approvalParams) return;
        setLoading(true);
        setApprovalParams(null);

        setMessages(prev => [...prev, { role: "user", content: approved ? "✅ Approved" : "❌ Rejected" }]);

        try {
            if (!token) {
                router.push("/login");
                return;
            }
            const res = await resumeChat(threadId, approvalParams.interruptId, approvalParams.approvalToken, approved, token);
            handleResponse(res);
        } catch (err) {
            toast.error("Resume failed");
        } finally {
            setLoading(false);
        }
    };

    const Logout = () => {
        clearSession();
        router.push("/login");
    };

    const getUserInitials = () => {
        if (!user?.name) return "U";
        return user.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
    };

    return (
        <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100">
            {/* Header */}
            <header className="flex items-center justify-between px-6 py-4 bg-white border-b shadow-sm">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-slate-800">SQLRAG Assistant</h1>
                            <p className="text-xs text-slate-500">AI-powered data assistant</p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    {user && (
                        <div className="flex items-center gap-3 px-4 py-2 bg-slate-50 rounded-xl">
                            <Avatar className="h-8 w-8 border-2 border-indigo-200">
                                <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-xs font-semibold">
                                    {getUserInitials()}
                                </AvatarFallback>
                            </Avatar>
                            <div className="hidden sm:block">
                                <p className="text-sm font-medium text-slate-700">{user.name}</p>
                                <div className="flex items-center gap-2">
                                    <Badge variant="secondary" className="text-xs px-2 py-0 bg-indigo-100 text-indigo-700 hover:bg-indigo-100">
                                        {role.charAt(0).toUpperCase() + role.slice(1)}
                                    </Badge>
                                </div>
                            </div>
                        </div>
                    )}
                    <Button variant="outline" onClick={Logout} className="text-slate-600 hover:text-slate-800">
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Logout
                    </Button>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-hidden flex flex-col p-4 max-w-5xl mx-auto w-full">
                <div
                    ref={chatContainerRef}
                    className="flex-1 overflow-y-auto rounded-2xl bg-white shadow-lg border border-slate-200 p-4 mb-4"
                    style={{ scrollBehavior: 'smooth' }}
                >
                    <div className="space-y-4 min-h-full">
                        {messages.length === 0 && (
                            <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center">
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center mb-4">
                                    <svg className="w-8 h-8 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-semibold text-slate-700 mb-2">Start a conversation</h3>
                                <p className="text-sm text-slate-500 max-w-md">
                                    Ask me about projects, tasks, team members, or financial data.
                                </p>
                            </div>
                        )}

                        {messages.map((m, i) => (
                            <div
                                key={i}
                                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2 duration-300`}
                            >
                                <div className={`flex gap-3 max-w-[90%] ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                                    <Avatar className={`h-8 w-8 flex-shrink-0 mt-1 ${m.role === "user" ? "" : "ring-2 ring-indigo-100"}`}>
                                        <AvatarFallback className={`text-xs font-semibold ${m.role === 'user'
                                            ? 'bg-gradient-to-br from-slate-700 to-slate-900 text-white'
                                            : 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white'
                                            }`}>
                                            {m.role === 'user' ? getUserInitials() : 'AI'}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className={`px-4 py-3 rounded-2xl ${m.role === "user"
                                        ? "bg-gradient-to-br from-slate-800 to-slate-900 text-white rounded-tr-sm"
                                        : "bg-slate-50 border border-slate-200 text-slate-800 rounded-tl-sm"
                                        }`}>
                                        {m.role === "user" ? (
                                            <p className="text-sm leading-relaxed">{m.content}</p>
                                        ) : (
                                            <div className="prose prose-sm prose-slate max-w-none 
                                                prose-headings:text-slate-800 prose-headings:font-semibold prose-headings:my-2
                                                prose-p:text-slate-700 prose-p:leading-relaxed prose-p:my-2
                                                prose-strong:text-slate-800 prose-strong:font-semibold
                                                prose-ul:my-2 prose-ul:pl-4 prose-li:text-slate-700 prose-li:my-0.5
                                                prose-ol:my-2 prose-ol:pl-4
                                                prose-table:my-3 prose-table:text-sm
                                                prose-th:bg-indigo-50 prose-th:text-indigo-800 prose-th:font-semibold prose-th:px-3 prose-th:py-2 prose-th:text-left prose-th:border prose-th:border-indigo-200
                                                prose-td:px-3 prose-td:py-2 prose-td:border prose-td:border-slate-200 prose-td:text-slate-700
                                                prose-tr:even:bg-slate-50
                                                prose-code:bg-slate-100 prose-code:text-indigo-600 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono
                                                prose-pre:bg-slate-800 prose-pre:text-slate-100 prose-pre:rounded-lg prose-pre:p-3 prose-pre:overflow-x-auto
                                            ">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                    {m.content}
                                                </ReactMarkdown>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}

                        {loading && (
                            <div className="flex justify-start animate-in fade-in duration-200">
                                <div className="flex gap-3">
                                    <Avatar className="h-8 w-8 ring-2 ring-indigo-100">
                                        <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-xs font-semibold">
                                            AI
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="px-4 py-4 rounded-2xl rounded-tl-sm bg-slate-50 border border-slate-200">
                                        <div className="flex items-center gap-2">
                                            <div className="flex items-center gap-1">
                                                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                            </div>
                                            <span className="text-xs text-slate-500 ml-2">Thinking...</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {approvalParams && (
                    <Card className="mb-4 border-2 border-amber-300 bg-gradient-to-r from-amber-50 to-yellow-50 shadow-lg animate-in fade-in slide-in-from-bottom-4 duration-300">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-md text-amber-800 flex items-center gap-2">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                Approval Required
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-sm text-amber-700">
                            The agent wants to execute changes. Please review the plan above and confirm.
                        </CardContent>
                        <CardFooter className="flex gap-2 justify-end pt-0">
                            <Button
                                variant="outline"
                                onClick={() => handleResume(false)}
                                className="border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
                            >
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                                Reject
                            </Button>
                            <Button
                                onClick={() => handleResume(true)}
                                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white"
                            >
                                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Approve
                            </Button>
                        </CardFooter>
                    </Card>
                )}

                <div className="flex gap-3 bg-white rounded-2xl shadow-lg border border-slate-200 p-2">
                    <Input
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                        placeholder="Type your message..."
                        disabled={loading || !!approvalParams}
                        className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent text-base placeholder:text-slate-400"
                    />
                    <Button
                        onClick={handleSend}
                        disabled={loading || !!approvalParams || !input.trim()}
                        className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-6 rounded-xl"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </Button>
                </div>
            </div>
        </div>
    );
}
