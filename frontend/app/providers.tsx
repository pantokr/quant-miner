"use client"

import { ChakraProvider, defaultSystem } from "@chakra-ui/react"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import { useState, useEffect } from "react"
import { Box } from "@chakra-ui/react"

export function Providers({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  return (
    <ChakraProvider value={defaultSystem}>
      <NextThemesProvider
        attribute="class"
        disableTransitionOnChange
        enableSystem={true}
        defaultTheme="system"
      >
        {mounted ? (
          <Box minH="100vh">
            {children}
          </Box>
        ) : (
          <Box minH="100vh" visibility="hidden">
            {children}
          </Box>
        )}
      </NextThemesProvider>
    </ChakraProvider>
  )
}
