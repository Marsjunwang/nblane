import { restoreProfiles } from "./profile_snapshot";

export default function globalTeardown(): void {
  restoreProfiles();
}
