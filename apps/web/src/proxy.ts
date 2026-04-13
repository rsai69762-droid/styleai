import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/navigation";
import { type NextRequest } from "next/server";

const intlMiddleware = createMiddleware(routing);

export async function proxy(request: NextRequest) {
  // Run i18n middleware first
  const response = intlMiddleware(request);

  // TODO: re-enable once Supabase connectivity is confirmed
  // try {
  //   const supabase = createServerClient(
  //     process.env.NEXT_PUBLIC_SUPABASE_URL!,
  //     process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  //     {
  //       cookies: {
  //         getAll() {
  //           return request.cookies.getAll();
  //         },
  //         setAll(cookiesToSet) {
  //           cookiesToSet.forEach(({ name, value, options }) => {
  //             response.cookies.set(name, value, options);
  //           });
  //         },
  //       },
  //     }
  //   );
  //   await supabase.auth.getUser();
  // } catch {
  //   // Supabase unreachable — continue without session refresh
  // }

  return response;
}

export const config = {
  matcher: ["/((?!_next|api|favicon.ico|.*\\..*).*)"],
};
