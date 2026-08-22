import type { CookieOptions, Request } from "express";

function isSecureRequest(req: Request) {
  if (req.protocol === "https") return true;

  const forwardedProto = req.headers["x-forwarded-proto"];
  if (!forwardedProto) return false;

  const protoList = Array.isArray(forwardedProto)
    ? forwardedProto
    : forwardedProto.split(",");

  return protoList.some(proto => proto.trim().toLowerCase() === "https");
}

export function getSessionCookieOptions(
  req: Request
): Pick<CookieOptions, "httpOnly" | "path" | "sameSite" | "secure"> {
  return {
    httpOnly: true,
    path: "/",
    // `lax` keeps the cookie on same-site requests and top-level navigations
    // while preventing it from riding along on cross-site subrequests (CSRF).
    // The Bearer-token fallback covers embedded-iframe browsers that block
    // third-party cookies.
    sameSite: "lax",
    secure: isSecureRequest(req),
  };
}
