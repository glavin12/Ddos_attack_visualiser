import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — DDoS Sentinel",
  description: "Real-time DDoS attack visualization operations center",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
