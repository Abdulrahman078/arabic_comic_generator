import "./globals.css";

export const metadata = {
  title: "مولد الكوميكس العربي",
  description: "Arabic AI Comic Generator",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ar" dir="rtl">
      <body className="antialiased">{children}</body>
    </html>
  );
}
