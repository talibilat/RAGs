"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/app/services/api";
import { setSession } from "@/app/services/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";

// Demo users for quick reference
const DEMO_USERS = [
    { email: "talib@example.com", name: "Talib Bilat", role: "admin" },
    { email: "sarah@example.com", name: "Sarah Chen", role: "admin" },
    { email: "bob@example.com", name: "Bob Johnson", role: "manager" },
    { email: "grace@example.com", name: "Grace Kim", role: "manager" },
    { email: "alice@example.com", name: "Alice Smith", role: "developer" },
    { email: "david@example.com", name: "David Lee", role: "developer" },
    { email: "frank@example.com", name: "Frank Miller", role: "developer" },
    { email: "carol@example.com", name: "Carol Williams", role: "designer" },
    { email: "emma@example.com", name: "Emma Garcia", role: "analyst" },
    { email: "henry@example.com", name: "Henry Wilson", role: "member" },
];

const getRoleBadgeColor = (role: string) => {
    switch (role) {
        case "admin": return "bg-red-100 text-red-700 border-red-200";
        case "manager": return "bg-blue-100 text-blue-700 border-blue-200";
        case "developer": return "bg-green-100 text-green-700 border-green-200";
        case "designer": return "bg-purple-100 text-purple-700 border-purple-200";
        case "analyst": return "bg-orange-100 text-orange-700 border-orange-200";
        default: return "bg-gray-100 text-gray-700 border-gray-200";
    }
};

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await login(email);
            setSession(data.token, { ...data.user, role: data.role });
            toast.success(`Welcome back, ${data.user.name}!`);
            router.push("/chat");
        } catch (err) {
            toast.error("Login failed. Check backend.");
        } finally {
            setLoading(false);
        }
    };

    const quickLogin = (userEmail: string) => {
        setEmail(userEmail);
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 p-4">
            <div className="flex flex-col lg:flex-row gap-6 max-w-4xl w-full">
                {/* Login Card */}
                <Card className="w-full lg:w-[380px] shadow-xl border-0">
                    <CardHeader className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-t-lg">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                                </svg>
                            </div>
                            <div>
                                <CardTitle className="text-xl">SQLRAG Assistant</CardTitle>
                                <CardDescription className="text-white/80">AI-powered data management</CardDescription>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="pt-6">
                        <form onSubmit={handleLogin} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="email" className="text-slate-700">Email Address</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="your@email.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="h-11"
                                />
                            </div>
                            <Button
                                type="submit"
                                className="w-full h-11 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700"
                                disabled={loading}
                            >
                                {loading ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                        Signing in...
                                    </span>
                                ) : "Sign In"}
                            </Button>
                        </form>

                        <div className="mt-6 pt-4 border-t">
                            <p className="text-xs text-slate-500 mb-3 flex items-center gap-1">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Only <strong className="text-red-600">admin</strong> users can approve write operations
                            </p>
                        </div>
                    </CardContent>
                </Card>

                {/* Users Table */}
                <Card className="flex-1 shadow-xl border-0">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-lg text-slate-700 flex items-center gap-2">
                            <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                            Demo Users
                        </CardTitle>
                        <CardDescription>Click any row to quick-fill email</CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                        <div className="border rounded-lg overflow-hidden">
                            <table className="w-full text-sm">
                                <thead className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white">
                                    <tr>
                                        <th className="px-3 py-2.5 text-left font-semibold">Name</th>
                                        <th className="px-3 py-2.5 text-left font-semibold">Email</th>
                                        <th className="px-3 py-2.5 text-left font-semibold">Role</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {DEMO_USERS.map((user, i) => (
                                        <tr
                                            key={user.email}
                                            onClick={() => quickLogin(user.email)}
                                            className={`cursor-pointer transition-colors hover:bg-indigo-50 ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50'} ${email === user.email ? 'bg-indigo-100' : ''}`}
                                        >
                                            <td className="px-3 py-2.5 font-medium text-slate-700">{user.name}</td>
                                            <td className="px-3 py-2.5 text-slate-600">{user.email}</td>
                                            <td className="px-3 py-2.5">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getRoleBadgeColor(user.role)}`}>
                                                    {user.role}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        <p className="text-xs text-slate-400 mt-3 text-center">
                            10 users • 8 projects • 15 tasks in demo database
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
