import './globals.css'
import { Providers } from './providers'

export const metadata = {
  title: 'UAE PPP Intelligence Portal',
  description: 'AI-powered UAE Public-Private Partnership project intelligence',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
