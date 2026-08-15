import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind class names, resolving conflicts (later classes win).
 * Standard shadcn/ui helper — components in /components/ui expect this
 * to exist at this exact path.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
