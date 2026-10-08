import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <span className="site-tab">Paper Archive</span>
        </header>
        {children}
      </body>
    </html>
  );
}