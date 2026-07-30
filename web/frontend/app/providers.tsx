"use client"

import { ChakraProvider, Box } from "@chakra-ui/react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { system } from "@/lib/theme"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider value={system}>
      <NextThemesProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <Box minH="100vh">{children}</Box>
      </NextThemesProvider>
    </ChakraProvider>
  )
}
