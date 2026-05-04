import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meridian — RE Credit Intelligence",
  description:
    "Market intelligence dashboard for residential RE credit underwriting. Aggregates supply, pricing, demographics, and permits across state, MSA, city, and ZIP.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
