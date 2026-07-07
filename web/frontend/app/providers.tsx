"use client"

import { ChakraProvider, defaultSystem, Box } from "@chakra-ui/react"
import { ThemeProvider as NextThemesProvider } from "next-themes"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider value={defaultSystem}>
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
