import { createTRPCReact } from "@trpc/react-query";
import type { AppRouter } from "../../../api/routers";

export const trpc = createTRPCReact<AppRouter>();
