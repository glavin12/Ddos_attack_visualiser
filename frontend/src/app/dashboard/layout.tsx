import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — Threat Observatory",
  description: "Real-time global threat intelligence dashboard",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
