import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

export const metadata: Metadata = {
  title: "Кулинарная лига — готовьте, пробуйте, делитесь",
  description: "Кулинарные задания для тех, кто любит готовить и открывать новое.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>
        <SiteHeader />
        {children}
        <footer className="site-footer">
          <span>Концепт-прототип · рабочее название не утверждено</span>
          <span>Сделано для тех, кто любит готовить</span>
        </footer>
      </body>
    </html>
  );
}
