/* Minimal typings for troika-three-text (the package ships none). Only the
 * surface the starmap uses is declared. */
declare module 'troika-three-text' {
  import type { Mesh, MeshBasicMaterial } from 'three';

  export class Text extends Mesh {
    text: string;
    font: string | undefined;
    fontSize: number;
    color: number | string;
    anchorX: 'left' | 'center' | 'right' | number;
    anchorY: 'top' | 'middle' | 'bottom' | number;
    outlineWidth: number | string;
    outlineColor: number | string;
    outlineOpacity: number;
    material: MeshBasicMaterial;
    textRenderInfo: { blockBounds: [number, number, number, number] } | null;
    sync(callback?: () => void): void;
    dispose(): void;
  }
}
