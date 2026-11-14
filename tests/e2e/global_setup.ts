import { assertOwnedStack } from "./runtime.mjs";

export default async function globalSetup(): Promise<void> {
  await assertOwnedStack();
}
