import { snapshotProfiles } from "./profile_snapshot";

export default function globalSetup(): void {
  snapshotProfiles();
}
