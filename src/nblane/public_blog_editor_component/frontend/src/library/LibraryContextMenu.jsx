import React, { useEffect, useMemo, useRef } from "react";
import {
  isParentableNode,
  isRootNode,
  isVirtualNode,
  libraryNodeTitle,
  libraryNodeType,
} from "./treeUtils.js";

function menuButton(item, index) {
  if (item.separator) {
    return <div key={`sep-${index}`} className="nb-library-menu-separator" />;
  }
  return (
    <button
      key={item.key}
      type="button"
      className={item.danger ? "is-danger" : ""}
      disabled={item.disabled}
      onClick={() => {
        if (!item.disabled) {
          item.onSelect?.();
        }
      }}
    >
      {item.label}
    </button>
  );
}

export function LibraryContextMenu({
  labels = {},
  menu,
  capabilities = {},
  canMutate = false,
  onClose,
  onAction,
}) {
  const menuRef = useRef(null);
  useEffect(() => {
    if (!menu) {
      return undefined;
    }
    const onPointer = (event) => {
      if (!menuRef.current?.contains(event.target)) {
        onClose?.();
      }
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose?.();
      }
    };
    window.addEventListener("pointerdown", onPointer);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("pointerdown", onPointer);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [menu, onClose]);

  const items = useMemo(() => {
    if (!menu?.node) {
      return [];
    }
    const node = menu.node;
    const type = libraryNodeType(node);
    const parentable = isParentableNode(node);
    const root = isRootNode(node);
    const virtual = isVirtualNode(node);
    const trashed = node.status === "trashed";
    const disabledBase = !canMutate || root || virtual;
    const make = (key, label, handler, disabled = false, danger = false) => ({
      key,
      label,
      disabled,
      danger,
      onSelect: () => {
        handler();
        onClose?.();
      },
    });
    const rows = [];
    if (!trashed && parentable && !virtual) {
      rows.push(
        make(
          "create-folder",
          labels.library_create_folder_here || labels.library_create_folder || "New folder here",
          () => onAction?.("create-folder", node),
          !canMutate || capabilities.create_folder === false,
        ),
        make(
          "create-post",
          labels.library_create_post_here || labels.library_create_post || "New post here",
          () => onAction?.("create-post", node),
          !canMutate || capabilities.create_post === false,
        ),
      );
    }
    if (!trashed) {
      if (virtual && type === "post") {
        rows.push(
          make(
            "attach-virtual",
            labels.library_attach_virtual || labels.library_attach_existing || "Add to library",
            () => onAction?.("attach-virtual", node),
            !canMutate || capabilities.attach_existing === false,
          ),
          { separator: true },
        );
      }
      rows.push(
        make(
          "attach",
          labels.library_attach_existing || "Attach ref",
          () => onAction?.("attach-existing", node),
          !canMutate || !parentable || virtual || capabilities.attach_existing === false,
        ),
        { separator: true },
        make(
          "rename",
          labels.library_rename || "Rename",
          () => onAction?.("rename", node),
          disabledBase || capabilities.rename_node === false,
        ),
        make(
          "move",
          labels.library_move_to || labels.library_move || "Move to",
          () => onAction?.("move", node),
          disabledBase || capabilities.move_node === false,
        ),
        make(
          "up",
          labels.library_up || "Up",
          () => onAction?.("reorder-up", node),
          disabledBase || capabilities.reorder_node === false,
        ),
        make(
          "down",
          labels.library_down || "Down",
          () => onAction?.("reorder-down", node),
          disabledBase || capabilities.reorder_node === false,
        ),
        make(
          "trash",
          labels.library_trash_node || "Trash",
          () => onAction?.("trash", node),
          disabledBase || capabilities.trash_node === false,
          true,
        ),
        { separator: true },
        make(
          "purge-active",
          labels.library_delete_forever || "Delete forever",
          () => onAction?.("purge-active", node),
          disabledBase || capabilities.permanent_delete_node === false,
          true,
        ),
      );
    } else {
      rows.push(
        make(
          "restore",
          labels.library_restore || "Restore",
          () => onAction?.("restore", node),
          !canMutate || capabilities.restore_node === false,
        ),
        make(
          "purge",
          labels.library_delete_forever || "Delete forever",
          () => onAction?.("purge-trash", node),
          !canMutate || capabilities.permanent_delete_node === false,
          true,
        ),
      );
    }
    if (type === "media") {
      rows.unshift(
        make(
          "insert-media",
          labels.insert_into_post || "Insert",
          () => onAction?.("insert-media", node),
          !canMutate,
        ),
        { separator: true },
      );
    }
    return rows;
  }, [canMutate, capabilities, labels, menu, onAction, onClose]);

  if (!menu?.node) {
    return null;
  }
  const style = {
    left: Math.max(8, Number(menu.x || 0)),
    top: Math.max(8, Number(menu.y || 0)),
  };
  return (
    <div
      ref={menuRef}
      className="nb-library-context-menu"
      style={style}
      role="menu"
      aria-label={libraryNodeTitle(menu.node)}
    >
      <div className="nb-library-context-title">{libraryNodeTitle(menu.node)}</div>
      {items.map(menuButton)}
    </div>
  );
}
