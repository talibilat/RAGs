import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50">
      <Card className="w-[400px] text-center">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">SQLRAG</CardTitle>
          <CardDescription>Agentic Project Management System</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-gray-500">
            Manage projects, tasks, and team members with an AI agent powered by LangGraph.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/login">
              <Button className="w-full">Login</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
