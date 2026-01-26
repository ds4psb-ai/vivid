"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

export function ModeToggle() {
    const { setTheme, resolvedTheme } = useTheme()
    const [mounted, setMounted] = React.useState(false)

    // Avoid hydration mismatch
    React.useEffect(() => {
        setMounted(true)
    }, [])

    if (!mounted) {
        return (
            <button className="relative rounded-full p-2 bg-black/5 dark:bg-white/10" title="Toggle theme">
                <span className="sr-only">Toggle theme</span>
                <div className="h-[1.2rem] w-[1.2rem]" />
            </button>
        )
    }

    const isDark = resolvedTheme === "dark"

    return (
        <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className={`
                relative rounded-full p-2
                bg-black/5 dark:bg-white/10
                hover:bg-black/10 dark:hover:bg-white/20
                active:scale-95
                transition-all duration-300 ease-out
                dark:hover:shadow-[0_0_12px_oklch(0.62_0.28_20_/_0.4)]
            `}
            title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
            <span className="sr-only">Toggle theme</span>
            <Sun
                className={`
                    h-[1.2rem] w-[1.2rem]
                    transition-all duration-300 ease-out
                    ${isDark ? "rotate-90 scale-0 opacity-0" : "rotate-0 scale-100 opacity-100"}
                `}
            />
            <Moon
                className={`
                    absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
                    h-[1.2rem] w-[1.2rem]
                    transition-all duration-300 ease-out
                    ${isDark ? "rotate-0 scale-100 opacity-100" : "rotate-90 scale-0 opacity-0"}
                `}
            />
        </button>
    )
}
