/** Atalho da busca: ⌘K no Mac, Ctrl K nos outros sistemas. */
export const ATALHO_BUSCA =
  typeof navigator !== "undefined" && /Mac|iPhone|iPad/i.test(navigator.platform || "") ? "⌘K" : "Ctrl K";
