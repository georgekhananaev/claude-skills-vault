e#!/usr/bin/env python3
"""
Next.js App Router Route Scaffolder

Generates a complete route folder with page, layout, loading, and error files.

Usage:
    python scaffold_route.py <route_path> [options]

Options:
    --with-layout     Include layout.tsx
    --with-loading    Include loading.tsx
    --with-error      Include error.tsx
    --with-action     Include actions.ts (Server Action)
    --dynamic         Use dynamic route [id]
    --output, -o      Output directory (default: current)

Examples:
    python scaffold_route.py dashboard
    python scaffold_route.py blog/[id] --dynamic --with-loading
    python scaffold_route.py settings --with-layout --with-action
"""

import argparse
import os
from pathlib import Path
from textwrap import dedent


def get_page_template(route_name: str, is_dynamic: bool) -> str:
    """Generate page.tsx content."""
    if is_dynamic:
        return dedent(f'''\
            import {{ Suspense }} from "react"
            import {{ Metadata }} from "next"
            import {{ notFound }} from "next/navigation"

            interface PageProps {{
              params: Promise<{{ id: string }}>
            }}

            export async function generateMetadata({{
              params,
            }}: PageProps): Promise<Metadata> {{
              const {{ id }} = await params
              // const item = await getItem(id)
              return {{
                title: `{route_name.title()} ${{id}}`,
              }}
            }}

            async function {route_name.title()}Content({{ id }}: {{ id: string }}) {{
              // const item = await db.items.findUnique({{ where: {{ id }} }})
              // if (!item) notFound()

              return (
                <div>
                  <h1>{route_name.title()} {{id}}</h1>
                  {{/* Render content */}}
                </div>
              )
            }}

            export default async function {route_name.title()}Page({{ params }}: PageProps) {{
              const {{ id }} = await params

              return (
                <main>
                  <Suspense fallback={{<{route_name.title()}Skeleton />}}>
                    <{route_name.title()}Content id={{id}} />
                  </Suspense>
                </main>
              )
            }}

            function {route_name.title()}Skeleton() {{
              return (
                <div className="animate-pulse">
                  <div className="h-8 bg-gray-200 rounded w-1/4 mb-4" />
                  <div className="h-4 bg-gray-200 rounded w-full mb-2" />
                </div>
              )
            }}
            ''')
    else:
        return dedent(f'''\
            import {{ Suspense }} from "react"
            import {{ Metadata }} from "next"

            export const metadata: Metadata = {{
              title: "{route_name.title()}",
              description: "{route_name.title()} page description",
            }}

            async function {route_name.title()}Content() {{
              // const data = await fetchData()

              return (
                <div>
                  <h1>{route_name.title()}</h1>
                  {{/* Render content */}}
                </div>
              )
            }}

            export default function {route_name.title()}Page() {{
              return (
                <main>
                  <Suspense fallback={{<{route_name.title()}Skeleton />}}>
                    <{route_name.title()}Content />
                  </Suspense>
                </main>
              )
            }}

            function {route_name.title()}Skeleton() {{
              return (
                <div className="animate-pulse">
                  <div className="h-8 bg-gray-200 rounded w-1/4 mb-4" />
                  <div className="h-4 bg-gray-200 rounded w-full mb-2" />
                </div>
              )
            }}
            ''')


def get_layout_template(route_name: str) -> str:
    """Generate layout.tsx content."""
    return dedent(f'''\
        interface {route_name.title()}LayoutProps {{
          children: React.ReactNode
        }}

        export default function {route_name.title()}Layout({{
          children,
        }}: {route_name.title()}LayoutProps) {{
          return (
            <div className="{route_name}-layout">
              {{/* Add navigation, sidebar, etc. */}}
              {{children}}
            </div>
          )
        }}
        ''')


def get_loading_template() -> str:
    """Generate loading.tsx content."""
    return dedent('''\
        export default function Loading() {
          return (
            <div className="animate-pulse space-y-4">
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-5/6" />
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/6" />
              </div>
            </div>
          )
        }
        ''')


def get_error_template() -> str:
    """Generate error.tsx content."""
    return dedent('''\
        "use client"

        import { useEffect } from "react"

        interface ErrorProps {
          error: Error & { digest?: string }
          reset: () => void
        }

        export default function Error({ error, reset }: ErrorProps) {
          useEffect(() => {
            console.error("[PAGE_ERROR]", error)
          }, [error])

          return (
            <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
              <h2 className="text-2xl font-bold">Something went wrong</h2>
              <p className="text-gray-600">{error.message}</p>
              <button
                onClick={reset}
                className="px-4 py-2 bg-blue-600 text-white rounded-md"
              >
                Try again
              </button>
            </div>
          )
        }
        ''')


def get_action_template(route_name: str) -> str:
    """Generate actions.ts content."""
    return dedent(f'''\
        "use server"

        import {{ z }} from "zod"
        import {{ auth }} from "@/lib/auth"
        import {{ revalidateTag }} from "next/cache"

        const {route_name.title()}Schema = z.object({{
          name: z.string().min(1).max(100),
        }})

        type ActionResult =
          | {{ success: true; id: string }}
          | {{ success: false; error: string }}

        export async function create{route_name.title()}(
          formData: FormData
        ): Promise<ActionResult> {{
          // 1. Rate limit
          // await rateLimit("create{route_name.title()}")

          // 2. Auth
          const session = await auth()
          if (!session?.user) {{
            return {{ success: false, error: "Unauthorized" }}
          }}

          // 3. Validate
          let validated
          try {{
            validated = {route_name.title()}Schema.parse({{
              name: formData.get("name"),
            }})
          }} catch {{
            return {{ success: false, error: "Invalid input" }}
          }}

          // 4. Authorization (if updating)

          // 5. Mutation
          // const item = await db.{route_name}s.create({{ data: validated }})

          // 6. Revalidate
          revalidateTag("{route_name}s")

          // 7. Audit log

          return {{ success: true, id: "new-id" }}
        }}
        ''')


def scaffold_route(
    route_path: str,
    output_dir: str,
    with_layout: bool,
    with_loading: bool,
    with_error: bool,
    with_action: bool,
    is_dynamic: bool,
) -> None:
    """Create route folder with all specified files."""
    # Parse route path
    parts = route_path.strip("/").split("/")
    route_name = parts[-1].replace("[", "").replace("]", "")

    # Create output path
    base_path = Path(output_dir) / "app" / route_path
    base_path.mkdir(parents=True, exist_ok=True)

    # Create files
    files_created = []

    # page.tsx (always)
    page_path = base_path / "page.tsx"
    page_path.write_text(get_page_template(route_name, is_dynamic))
    files_created.append(page_path)

    # Optional files
    if with_layout:
        layout_path = base_path / "layout.tsx"
        layout_path.write_text(get_layout_template(route_name))
        files_created.append(layout_path)

    if with_loading:
        loading_path = base_path / "loading.tsx"
        loading_path.write_text(get_loading_template())
        files_created.append(loading_path)

    if with_error:
        error_path = base_path / "error.tsx"
        error_path.write_text(get_error_template())
        files_created.append(error_path)

    if with_action:
        action_path = base_path / "actions.ts"
        action_path.write_text(get_action_template(route_name))
        files_created.append(action_path)

    # Print summary
    print(f"\nRoute scaffolded: {route_path}")
    print("-" * 40)
    for f in files_created:
        print(f"  Created: {f}")

    print(f"\nRoute will be accessible at: /{route_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold Next.js App Router route"
    )
    parser.add_argument("route_path", help="Route path (e.g., dashboard, blog/[id])")
    parser.add_argument("--with-layout", action="store_true", help="Include layout.tsx")
    parser.add_argument("--with-loading", action="store_true", help="Include loading.tsx")
    parser.add_argument("--with-error", action="store_true", help="Include error.tsx")
    parser.add_argument("--with-action", action="store_true", help="Include actions.ts")
    parser.add_argument("--dynamic", action="store_true", help="Dynamic route with [id]")
    parser.add_argument("--output", "-o", default=".", help="Output directory")

    args = parser.parse_args()

    scaffold_route(
        route_path=args.route_path,
        output_dir=args.output,
        with_layout=args.with_layout,
        with_loading=args.with_loading,
        with_error=args.with_error,
        with_action=args.with_action,
        is_dynamic=args.dynamic or "[" in args.route_path,
    )


if __name__ == "__main__":
    main()